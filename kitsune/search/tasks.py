import datetime
import logging
import sys
import traceback

from celery import task
from django.apps import apps
from django_elasticsearch_dsl.registries import registry
from django_statsd.clients import statsd
from multidb.pinning import pin_this_thread, unpin_this_thread

from kitsune.search.es_utils import (index_chunk, UnindexMeBro, write_index,
                                     get_analysis, es_analyzer_for_locale)
from kitsune.search.utils import from_class_path
from kitsune.sumo.decorators import timeit

log = logging.getLogger(__name__)

# from elasticutils.contrib.django import get_es


# This is present in memcached when reindexing is in progress and
# holds the number of outstanding index chunks. Once it hits 0,
# indexing is done.
OUTSTANDING_INDEX_CHUNKS = 'search:outstanding_index_chunks'

CHUNK_SIZE = 50000

log = logging.getLogger('k.task')


class IndexingTaskError(Exception):
    """Exception that captures current exception information

    Some exceptions aren't pickleable. This uses traceback module to
    format the exception that's currently being thrown and tosses it
    in the message of IndexingTaskError at the time the
    IndexingTaskError is created.

    So you can do this::

        try:
            # some code that throws an error
        except Exception as exc:
            raise IndexingTaskError()

    The message will have the message and traceback from the original
    exception thrown.

    Yes, this is goofy.

    """
    def __init__(self):
        super(IndexingTaskError, self).__init__(traceback.format_exc())


@task()
@timeit
def index_chunk_task(write_index, batch_id, rec_id, chunk):
    """Index a chunk of things.

    :arg write_index: the name of the index to index to
    :arg batch_id: the name for the batch this chunk belongs to
    :arg rec_id: the id for the record for this task
    :arg chunk: a (class, id_list) of things to index
    """
    cls_path, id_list = chunk
    cls = from_class_path(cls_path)
    rec = None

    # Need to import Record here to prevent circular import
    from kitsune.search.models import Record

    try:
        # Pin to master db to avoid replication lag issues and stale data.
        pin_this_thread()

        # Update record data.
        rec = Record.objects.get(pk=rec_id)
        rec.start_time = datetime.datetime.now()
        rec.message = u'Reindexing into %s' % write_index
        rec.status = Record.STATUS_IN_PROGRESS
        rec.save()

        index_chunk(cls, id_list, reraise=True)
        rec.mark_success()

    except Exception:
        if rec is not None:
            rec.mark_fail(u'Errored out %s %s' % (sys.exc_type, sys.exc_value))

        log.exception('Error while indexing a chunk')
        # Some exceptions aren't pickleable and we need this to throw
        # things that are pickleable.
        raise IndexingTaskError()

    finally:
        unpin_this_thread()


# Note: If you reduce the length of RETRY_TIMES, it affects all tasks
# currently in the celery queue---they'll throw an IndexError.
RETRY_TIMES = (
    60,           # 1 minute
    5 * 60,       # 5 minutes
    10 * 60,      # 10 minutes
    30 * 60,      # 30 minutes
    60 * 60,      # 60 minutes
    )
MAX_RETRIES = len(RETRY_TIMES)


@task()
@timeit
def index_task(cls, id_list, **kw):
    """Index documents specified by cls and ids"""
    statsd.incr('search.tasks.index_task.%s' % cls.get_mapping_type_name())
    try:
        # Pin to master db to avoid replication lag issues and stale
        # data.
        pin_this_thread()

        qs = cls.get_model().objects.filter(pk__in=id_list).values_list(
            'pk', flat=True)
        for id_ in qs:
            try:
                cls.index(cls.extract_document(id_), id_=id_)
            except UnindexMeBro:
                # If extract_document throws this, then we need to
                # remove this item from the index.
                cls.unindex(id_)

    except Exception as exc:
        retries = index_task.request.retries
        if retries >= MAX_RETRIES:
            # Some exceptions aren't pickleable and we need this to
            # throw things that are pickleable.
            raise IndexingTaskError()

        statsd.incr('search.tasks.index_task.retry', 1)
        statsd.incr('search.tasks.index_task.retry%d' % RETRY_TIMES[retries],
                    1)

        index_task.retry(exc=exc, max_retries=MAX_RETRIES,
                         countdown=RETRY_TIMES[retries])
    finally:
        unpin_this_thread()


@task()
@timeit
def unindex_task(cls, id_list, **kw):
    """Unindex documents specified by cls and ids"""
    statsd.incr('search.tasks.unindex_task.%s' % cls.get_mapping_type_name())
    try:
        # Pin to master db to avoid replication lag issues and stale
        # data.
        pin_this_thread()
        for id_ in id_list:
            cls.unindex(id_)
    except Exception as exc:
        retries = unindex_task.request.retries
        if retries >= MAX_RETRIES:
            # Some exceptions aren't pickleable and we need this to
            # throw things that are pickleable.
            raise IndexingTaskError()

        statsd.incr('search.tasks.unindex_task.retry', 1)
        statsd.incr('search.tasks.unindex_task.retry%d' % RETRY_TIMES[retries],
                    1)

        unindex_task.retry(exc=exc, max_retries=MAX_RETRIES,
                           countdown=RETRY_TIMES[retries])
    finally:
        unpin_this_thread()


@task()
@timeit
def update_synonyms_task():
    es = get_es()  # noqa

    # Close the index, update the settings, then re-open it.
    # This will cause search to be unavailable for a few seconds.
    # This updates all of the analyzer settings, which is kind of overkill,
    # but will make sure everything stays consistent.
    index = write_index('default')
    analysis = get_analysis()

    # if anything goes wrong, it is very important to re-open the index.
    try:
        es.indices.close(index)
        es.indices.put_settings(index=index, body={
            'analysis': analysis,
        })
    finally:
        es.indices.open(index)


def _get_index(model, index_name):
    """
    Get Index from all the indices
    :param indices: DED indices list
    :param index_name: Name of the index
    :return: DED Index
    """
    indices = registry.get_indices(models=[model])
    for index in indices:
        if str(index) == index_name:
            return index


def _get_document(model, document_class):
    """
    Get DED document class object from the model and name of document class
    :param model: The model class to find the document
    :param document_class: the name of the document class.
    :return: DED DocType object
    """
    documents = registry.get_documents(models=[model])

    for document in documents:
        if str(document) == document_class:
            return document


@task()
def create_new_es_index(app_label, model_name, document_class, new_index_name, locale):
    model = apps.get_model(app_label, model_name)
    es_document = _get_document(model=model, document_class=document_class)
    base_index = es_document._doc_type.index
    base_index_obj = _get_index(model, base_index)
    new_index = base_index_obj.clone(name=new_index_name)
    # Get analyzer for the locale and add it to index
    analyzer = es_analyzer_for_locale(locale)
    new_index.analyzer(analyzer)
    new_index.create()
    log.info("Successfully created new index {}".format(new_index_name))


@task()
def switch_es_index(app_label, model_name, document_class, index_alias, new_index_name):
    """
    Add alias to newly created index and remove the old indexes
     This is done in atomic, so the search dont get any downtime
    :param app_label: App label of the model
    :param model_name: Model class name
    :param document_class: DED DocType class in string
    :param index_alias: The alias used for finding the old indexes.
                        Its also added to newly created index.
    :param new_index_name: The newly created index name
    :return:
    """
    model = apps.get_model(app_label, model_name)
    es_document = _get_document(model=model, document_class=document_class)

    base_index = es_document._doc_type.index
    base_index_obj = _get_index(model, base_index)
    # Alias can not be used to delete an index.
    # https://www.elastic.co/guide/en/elasticsearch/reference/6.0/indices-delete-index.html
    # So get the old indexes to delete it
    old_indexes = base_index_obj.connection.indices.get(index=index_alias, ignore_unavailable=True)
    all_aliases = [index_alias, base_index]

    alias_actions = [dict(add=dict(index=new_index_name, alias=alias))
                     for alias in all_aliases]

    if old_indexes:
        remove_alias_actions = dict(remove_index=dict(indices=old_indexes.keys()))
        alias_actions.append(remove_alias_actions)

    base_index_obj.connection.indices.update_aliases(dict(actions=alias_actions))

    message = ("Successfully deleted {old_index_num} indexes and add {aliases} aliases "
               "to {new_index} index")

    log.info(message.format(old_index_num=len(old_indexes),
                            new_index=new_index_name, aliases=all_aliases))


@task()
def index_objects_to_es(app_label, model_name, document_class, index_name, objects_id):
    model = apps.get_model(app_label, model_name)
    document = _get_document(model=model, document_class=document_class)

    # Use queryset from model as the ids are specific
    queryset = model.objects.all().filter(id__in=objects_id).iterator()
    log.info("Indexing model: {}, id:'{}' index {}".format(model.__name__, objects_id, index_name))
    document().update(queryset, index_name=index_name)


@task()
def index_missing_objects(app_label, model_name, document_class, index_generation_time, locale):
    """
    Task to insure that none of the object is missed from indexing.
    The index generation time is passed.
    While the task is running, new objects can be created/deleted in database
    and they will not be in the tasks for indexing into ES.
    This task will index all the objects that got into DB after the `index_generation_time`
    timestamp to ensure that everything is in ES index.
    """
    model = apps.get_model(app_label, model_name)
    document = _get_document(model=model, document_class=document_class)
    # TODO: Make it more generic
    if model_name == 'Document':
        queryset = (document().get_queryset()
                              .exclude(current_revision__created__lte=index_generation_time))
    else:
        queryset = document().get_queryset().exclude(created__lte=index_generation_time)

    if locale:
        locale_field = getattr(document, 'locale_field', 'locale')
        locale_filter = {locale_field: locale}
        queryset = queryset.filter(**locale_filter)

    document().update(queryset.iterator())

    log.info("Indexed {} missing objects from model: {}'".format(queryset.count(), model.__name__))
    # TODO: Figure out how to remove the objects from ES index that has been deleted
