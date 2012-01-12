import elasticutils
import logging
import pyes
from threading import local

from django.conf import settings
from django.core import signals
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from search.tasks import index_task, unindex_task

log = logging.getLogger('es_search')


# db_table name -> model Class for search models
_search_models = {}


def get_search_models():
    """Returns a list of model classes"""
    # TODO: if we do weakrefs, then we should remove dead refs here.

    values = _search_models.values()

    # Sort to stabilize.
    values.sort(key=lambda cls: cls._meta.db_table)
    return values


_local_tasks = local()
_local_tasks.es_index_task_set = set()


class SearchMixin(object):
    """A mixin which adds ES indexing support for the model

    When using this mixin, make sure to implement:

    * get_mapping
    * extract_document

    Additionally, after defining your model, register it as a
    search model::

         MyModel.register_search_model()

    """
    @classmethod
    def register_search_model(cls):
        """Register a model as participating in full reindexing and statistic
        gathering"""
        # TODO: Fix this to use weakrefs
        _search_models[cls._meta.db_table] = cls

    @classmethod
    def get_mapping(self):
        """Returns the ES mapping defition for this document type

        This must be implemented. It should return an ES mapping.

        For examples, see the codebase.

        """
        raise NotImplementedError

    def extract_document(self):
        """Extracts the ES index document for this instance

        This must be implemented. It should return a dict representing
        the document to be indexed.

        For examples, see the codebase.

        """
        raise NotImplementedError

    @classmethod
    def _get_index(cls):
        """Returns the index for this class"""
        indexes = settings.ES_INDEXES
        return indexes.get(cls._meta.db_table) or indexes['default']

    @classmethod
    def add_index_task(cls, ids):
        """Adds an index task.

        :arg ids: tuple of ids

        """
        _local_tasks.es_index_task_set.add((index_task.delay, (cls, ids)))

    @classmethod
    def add_unindex_task(cls, ids):
        """Creates a task to remove this document from the ES index

        :arg ids: tuple of ids

        """
        _local_tasks.es_index_task_set.add((unindex_task.delay, (cls, ids)))

    @classmethod
    def index(cls, document, bulk=False, force_insert=False, refresh=False,
              es=None):
        """Indexes a single document"""
        if not settings.ES_LIVE_INDEXING:
            return

        if es is None:
            es = elasticutils.get_es()

        index = cls._get_index()
        doc_type = cls._meta.db_table

        # TODO: handle pyes.urllib3.TimeoutErrors here.
        es.index(document, index=index, doc_type=doc_type, id=document['id'],
                 bulk=bulk, force_insert=force_insert)

        if refresh:
            es.refresh(timesleep=0)

    @classmethod
    def unindex(cls, id):
        """Removes a document from the index"""
        if not settings.ES_LIVE_INDEXING:
            return

        index = cls._get_index()
        doc_type = cls._meta.db_table
        try:
            elasticutils.get_es().delete(index, doc_type, id)
        except pyes.exceptions.NotFoundException:
            # Ignore the case where we try to delete something that's
            # not there.
            pass


def register_live_indexers(sender_class,
                           app,
                           instance_to_indexee=lambda s: s):
    """Register signal handlers to keep the index up to date for a model.

    :arg sender_class: The class to listen for saves and deletes on
    :arg app: A bit of UID we use to build the signal handlers' dispatch_uids. This is prepended to the ``sender_class`` model name, "elastic", and the signal name, so it should combine with those to make something unique. For this reason, the app name is usually a good choice, yielding something like "wiki.TaggedItem.elastic.post_save".
    :arg instance_to_indexee: A callable which takes the signal sender and returns the model instance to be indexed. The returned instance should be a subclass of SearchMixin. If the callable returns None, no indexing is performed. Default: a callable which returns the sender itself.

    """
    def updater(sender, instance, **kw):
        """Return a callable that files an add-to-index task."""
        obj = instance_to_indexee(instance)
        if obj is not None and not kw.get('raw'):
            obj.add_index_task((obj.id,))  # TODO: Make this an instance method?

    def deleter(sender, instance, **kw):
        """Return a callable that files a delete-from-index task."""
        obj = instance_to_indexee(instance)
        if obj is not None and not kw.get('raw'):
            obj.add_unindex_task((obj.id,))

    def indexing_receiver(signal, signal_name):
        """Return a routine that registers signal handlers for indexers.

        The returned registration routine uses strong refs, makes up a
        dispatch_uid, and uses ``sender_class`` as the sender.

        """
        return receiver(
                signal,
                sender=sender_class,
                dispatch_uid='%s.%s.elastic.%s' %
                             (app, sender_class.__name__, signal_name),
                weak=False)

    indexing_receiver(post_save, 'post_save')(updater)
    indexing_receiver(pre_delete, 'pre_delete')(deleter)


def generate_tasks(**kwargs):
    """Goes through thread local index update tasks set and generates
    celery tasks for all tasks in the set.

    Because this works off of a set, it naturally de-dupes the tasks,
    so if four tasks get tossed into the set that are identical, we
    execute it only once.

    """
    lt = _local_tasks
    for fun, args in lt.es_index_task_set:
        fun(*args)

    lt.es_index_task_set.clear()


signals.request_finished.connect(generate_tasks)
