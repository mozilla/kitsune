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

    def index_later(self):
        """Register myself to be indexed at the end of the request."""
        _local_tasks().add((index_task.delay, (self.__class__, (self.id,))))


    def unindex_later(self):
        """Register myself to be unindexed at the end of the request."""
        _local_tasks().add((unindex_task.delay, (self.__class__, (self.id,))))

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
