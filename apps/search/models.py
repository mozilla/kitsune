import elasticutils
import logging
import pyes
import time
from threading import local

from django.conf import settings
from django.core import signals
from django.db import reset_queries
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from search.tasks import index_task, unindex_task
from search import es_utils
from search.es_utils import INDEX_SETTINGS

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


# Holds a threadlocal set of indexing tasks to be filed after the request.
_local = local()


def _local_tasks():
    """(Create and) return the threadlocal set of indexing tasks."""
    if getattr(_local, 'tasks', None) is None:
        _local.tasks = set()
    return _local.tasks


class SearchMixin(object):
    """A mixin which adds ES indexing support for the model

    When using this mixin, make sure to implement:

    * get_mapping
    * extract_document

    Additionally, after defining your model, remember to register it and any
    related models which affect it::

         register_for_indexing(MyModel, 'some_app')
         register_for_indexing(RelatedModel, 'some_app',
                                instance_to_indexee=lambda r: r.my_model)

    """
    @classmethod
    def get_mapping(self):
        """Returns the ES mapping definition for this document type

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
    def get_es_index(cls):
        """Returns the index for this class"""
        indexes = settings.ES_INDEXES
        return indexes.get(cls._meta.db_table) or indexes['default']

    def index_later(self):
        """Register myself to be indexed at the end of the request."""
        _local_tasks().add((index_task.delay, (self.__class__, (self.id,))))

    def unindex_later(self):
        """Register myself to be unindexed at the end of the request."""
        _local_tasks().add((unindex_task.delay, (self.__class__, (self.id,))))

    @classmethod
    def index_all(cls, percent=100):
        """Reindexes all the objects for this model.

        Yields number of documents done.

        Note: This can get run from the command line, so we log stuff
        to let the user know what's going on.

        :arg percent: The percentage of questions to index. Defaults to
            100--e.g. all of them.

        """
        es = es_utils.get_es()

        doc_type = cls._meta.db_table
        index = cls.get_es_index()

        if index != settings.ES_INDEXES.get('default'):
            # If this doctype isn't using the default index, then this
            # doctype is responsible for deleting and re-creating the
            # index.
            es.delete_index_if_exists(index)
            es.create_index(index, settings=INDEX_SETTINGS)

        start_time = time.time()

        log.info('reindex %s into %s index', doc_type, index)

        log.info('setting up mapping....')
        mapping = cls.get_mapping()
        es.put_mapping(doc_type, mapping, index)

        log.info('iterating through %s....', doc_type)
        total = cls.objects.count()
        to_index = int(total * (percent / 100.0))
        log.info('total %s: %s (to be indexed: %s)', doc_type, total, to_index)
        total = to_index

        # Some models have a gazillion instances. So we want to go
        # through them one at a time in a way that doesn't pull all
        # the data into memory all at once. So we iterate through ids
        # and pull the objects one at a time.
        qs = cls.objects.order_by('id').values_list('id', flat=True)

        for t, obj_id in enumerate(qs.iterator()):
            if t > total:
                break

            obj = cls.objects.get(pk=obj_id)

            if t % 1000 == 0 and t > 0:
                time_to_go = (total - t) * ((time.time() - start_time) / t)
                log.info('%s/%s... (%s to go)', t, total,
                         es_utils.format_time(time_to_go))

                # We call this every 1000 or so because we're
                # essentially loading the whole db and if DEBUG=True,
                # then Django saves every sql statement which causes
                # our memory to go up up up. So we reset it and that
                # makes things happier even in DEBUG environments.
                reset_queries()

            if t % settings.ES_FLUSH_BULK_EVERY == 0:
                # We built the ES with this setting, but it doesn't
                # actually do anything with it unless we call
                # flush_bulk which causes it to check its bulk_size
                # and flush it if it's too big.
                es.flush_bulk()

            try:
                cls.index(obj.extract_document(), bulk=True, es=es)
            except Exception:
                log.exception('Unable to extract/index document (id: %d)',
                              obj.id)

            yield t

        es.flush_bulk(forced=True)
        end_time = time.time()
        log.info('done! (%s)', es_utils.format_time(end_time - start_time))
        es.refresh()

    @classmethod
    def index(cls, document, bulk=False, force_insert=False, refresh=False,
              es=None):
        """Indexes a single document"""
        if not settings.ES_LIVE_INDEXING:
            return

        if es is None:
            es = elasticutils.get_es()

        index = cls.get_es_index()
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

        index = cls.get_es_index()
        doc_type = cls._meta.db_table
        try:
            elasticutils.get_es().delete(index, doc_type, id)
        except pyes.exceptions.NotFoundException:
            # Ignore the case where we try to delete something that's
            # not there.
            pass


_identity = lambda s: s


def register_for_indexing(sender_class,
                          app,
                          instance_to_indexee=_identity):
    """Register a model whose changes might invalidate ElasticSearch indexes.

    Specifically, each time an instance of this model is saved or deleted, the
    index might need to be updated. Registers the model as participating in
    full indexing, statistics gathering, and live indexing, as appropriate.

    :arg sender_class: The class to listen for saves and deletes on
    :arg app: A bit of UID we use to build the signal handlers' dispatch_uids.
        This is prepended to the ``sender_class`` model name, "elastic", and
        the signal name, so it should combine with those to make something
        unique. For this reason, the app name is usually a good choice,
        yielding something like "wiki.TaggedItem.elastic.post_save".
    :arg instance_to_indexee: A callable which takes the signalling instance
        and returns the model instance to be indexed. The returned instance
        should be a subclass of SearchMixin. If the callable returns None, no
        indexing is performed. Default: a callable which returns the sender
        itself.

    """
    def maybe_call_method(instance, is_raw, method_name):
        """Call an (un-)indexing method on instance if appropriate."""
        obj = instance_to_indexee(instance)
        if obj is not None and not is_raw:
            getattr(obj, method_name)()

    def update(sender, instance, **kw):
        """File an add-to-index task for the indicated object."""
        maybe_call_method(instance, kw.get('raw'), 'index_later')

    def delete(sender, instance, **kw):
        """File a remove-from-index task for the indicated object."""
        maybe_call_method(instance, kw.get('raw'), 'unindex_later')

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

    # Register a model as participating in full reindexing and statistics
    # gathering. TODO: Fix this to use weakrefs.
    if instance_to_indexee is _identity:
        # Register only the model that "is" the ES doc, not related ones:
        _search_models[sender_class._meta.db_table] = sender_class

    # Register signal listeners to keep indexes up to date:
    indexing_receiver(post_save, 'post_save')(update)
    indexing_receiver(pre_delete, 'pre_delete')(
        # If it's the indexed instance that's been deleted, go ahead and delete
        # it from the index. Otherwise, we just want to update whatever model
        # it's related to.
        delete if instance_to_indexee is _identity else update)


def generate_tasks(**kwargs):
    """Goes through thread local index update tasks set and generates
    celery tasks for all tasks in the set.

    Because this works off of a set, it naturally de-dupes the tasks,
    so if four tasks get tossed into the set that are identical, we
    execute it only once.

    """
    tasks = _local_tasks()
    for fun, args in tasks:
        fun(*args)

    tasks.clear()


signals.request_finished.connect(generate_tasks)
