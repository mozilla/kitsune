import logging
import pyes
from threading import local

from django.conf import settings
from django.core import signals
from django.db import models
from django.db.models.signals import pre_delete, post_save, m2m_changed
from django.dispatch import receiver

from elasticutils import MLT

from search import es_utils
from search.es_utils import ESTimeoutError, ESMaxRetryError, ESException
from search.tasks import index_task, unindex_task
from sumo.models import ModelBase

log = logging.getLogger('k.search.es')


# db_table name -> model Class for search models
_search_models = {}


def get_search_models(models=None):
    """Returns a list of model classes"""
    # TODO: if we do weakrefs, then we should remove dead refs here.

    if models is None:
        values = _search_models.values()
    else:
        values = [_search_models[name] for name in models]

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
        """Return the ES mapping properties for this document type.

        For example... ::

            {'id': {'type': 'integer'}, ...}

        """
        raise NotImplementedError

    @classmethod
    def extract_document(cls, obj_id):
        """Extracts the ES index document for this instance

        This must be implemented. It should return a dict representing
        the document to be indexed.

        For examples, see the codebase.

        """
        raise NotImplementedError

    @classmethod
    def get_model_name(cls):
        """Returns model name for this model class

        By default this is ``cls._meta.db_table``.
        """
        return cls._meta.db_table

    @classmethod
    def search(cls):
        """Returns an S for this class

        This applies a filter on doctype=cls._meta.db_table which
        makes sure to return results specific to this class.
        """
        return es_utils.Sphilastic(cls).filter(model=cls.get_model_name())

    def index_later(self):
        """Register myself to be indexed at the end of the request."""
        _local_tasks().add((index_task.delay, (self.__class__, (self.id,))))

    def unindex_later(self):
        """Register myself to be unindexed at the end of the request."""
        _local_tasks().add((unindex_task.delay, (self.__class__, (self.id,))))

    @classmethod
    def get_query_fields(cls):
        return []

    @classmethod
    def get_indexable(cls):
        # Some models have a gazillion instances. So we want to go
        # through them one at a time in a way that doesn't pull all
        # the data into memory all at once. So we iterate through ids
        # and pull the objects one at a time.
        return cls.objects.order_by('id').values_list('id', flat=True)

    @classmethod
    def get_document_id(cls, id_):
        """Generates a composed elasticsearch document id"""
        return '%s:%s' % (cls.get_model_name(), id_)

    @classmethod
    def index(cls, document, bulk=False, force_insert=False, refresh=False,
              es=None):
        """Indexes a single document"""
        if not settings.ES_LIVE_INDEXING:
            return

        if es is None:
            # Use es_utils.get_indexing_es() because it uses
            # ES_INDEXING_TIMEOUT.
            es = es_utils.get_indexing_es()

        es.index(document,
                 index=es_utils.WRITE_INDEX,
                 doc_type=es_utils.SUMO_DOCTYPE,
                 id=cls.get_document_id(document['id']),
                 bulk=bulk,
                 force_insert=force_insert)

        if refresh:
            es.refresh(es_utils.WRITE_INDEX, timesleep=0)

    @classmethod
    def unindex(cls, id_, es=None):
        """Removes a document from the index"""
        if not settings.ES_LIVE_INDEXING:
            return

        if es is None:
            # Use es_utils.get_indexing_es() because it uses
            # ES_INDEXING_TIMEOUT.
            es = es_utils.get_indexing_es()

        try:
            es.delete(es_utils.WRITE_INDEX, es_utils.SUMO_DOCTYPE,
                      cls.get_document_id(id_))

            # Refresh after the delete, but only if the delete was
            # successful.
            es.refresh(es_utils.WRITE_INDEX, timesleep=0)
        except pyes.exceptions.NotFoundException:
            # Ignore the case where we try to delete something that's
            # not there.
            pass

    @classmethod
    def get_s(cls):
        """Get an S."""
        return es_utils.Sphilastic(object).values_dict()

    @classmethod
    def morelikethis(cls, id_, s, fields):
        """morelikethis query."""
        try:
            return list(MLT(
                id_, s=s, fields=fields, min_term_freq=1, min_doc_freq=1))
        except (ESTimeoutError, ESMaxRetryError, ESException):
            return []


_identity = lambda s: s


def register_for_indexing(sender_class,
                          app,
                          instance_to_indexee=_identity,
                          m2m=False):
    """Register a model whose changes might invalidate ElasticSearch
    indexes.

    Specifically, each time an instance of this model is saved or
    deleted, the index might need to be updated. Registers the model
    as participating in full indexing, statistics gathering, and live
    indexing, as appropriate.

    :arg sender_class: The class to listen for saves and deletes on
    :arg app: A bit of UID we use to build the signal handlers'
        dispatch_uids.  This is prepended to the ``sender_class``
        model name, "elastic", and the signal name, so it should
        combine with those to make something unique. For this reason,
        the app name is usually a good choice, yielding something like
        "wiki.TaggedItem.elastic.post_save".
    :arg instance_to_indexee: A callable which takes the signalling
        instance and returns the model instance to be indexed. The
        returned instance should be a subclass of SearchMixin. If the
        callable returns None, no indexing is performed. Default: a
        callable which returns the sender itself.

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
    # TODO: Untangle this mess - Bug 778753
    if m2m:
        indexing_receiver(m2m_changed, 'm2m_changed')(update)
    else:
        indexing_receiver(post_save, 'post_save')(update)

        indexing_receiver(pre_delete, 'pre_delete')(
            # If it's the indexed instance that's been deleted, go ahead
            # and delete it from the index. Otherwise, we just want to
            # update whatever model it's related to.
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


class Record(ModelBase):
    """Record for the reindexing log"""
    starttime = models.DateTimeField(null=True)
    endtime = models.DateTimeField(null=True)
    text = models.CharField(max_length=255)

    class Meta:
        permissions = (
            ('reindex', 'Can run a full reindexing'),
            )

    def delta(self):
        """Returns the timedelta"""
        if self.starttime and self.endtime:
            return self.endtime - self.starttime
        return None
