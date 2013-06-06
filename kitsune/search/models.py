import logging
from threading import local

from django.conf import settings
from django.core import signals
from django.db import models
from django.db.models.signals import pre_delete, post_save, m2m_changed
from django.dispatch import receiver

from elasticutils.contrib.django import MappingType, Indexable, MLT
from pyelasticsearch.exceptions import ElasticHttpNotFoundError

from kitsune.search import es_utils
from kitsune.search.tasks import index_task, unindex_task
from kitsune.sumo.models import ModelBase

log = logging.getLogger('k.search.es')


# db_table_name -> MappingType class
_search_mapping_types = {}


def get_mapping_types(mapping_types=None):
    """Returns a list of MappingTypes"""
    if mapping_types is None:
        values = _search_mapping_types.values()
    else:
        values = [_search_mapping_types[name] for name in mapping_types]

    # Sort to stabilize
    values.sort(key=lambda cls: cls.get_mapping_type_name())
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

    * get_mapping_type

    Additionally, after defining your model, remember to register it and any
    related models which affect it::

         register_for_indexing(MyModel, 'some_app')
         register_for_indexing(RelatedModel, 'some_app',
                                instance_to_indexee=lambda r: r.my_model)

    """
    @classmethod
    def get_mapping_type(cls):
        """Return the MappingType for this model"""
        raise NotImplementedError

    def index_later(self):
        """Register myself to be indexed at the end of the request."""
        _local_tasks().add((index_task.delay, (
                    self.get_mapping_type(), (self.id,))))

    def unindex_later(self):
        """Register myself to be unindexed at the end of the request."""
        _local_tasks().add((unindex_task.delay, (
                    self.get_mapping_type(), (self.id,))))


class SearchMappingType(MappingType, Indexable):
    """Contains helpers on top of what ElasticUtils provides

    Subclasses should implement the following:

    1. get_mapping needs to return {'properties': { ... fields ... }}
    2. get_query_fields should return a list of fields for query
    3. extract_document
    4. get_model
    5. the mapping type class should be decorated with
       ``@register_mapping_type``

    Then make sure to:

    6. implement get_mapping_type on the related model

    """
    @classmethod
    def search(cls):
        return es_utils.Sphilastic(cls)

    @classmethod
    def get_index(cls):
        return es_utils.WRITE_INDEX

    @classmethod
    def get_query_fields(cls):
        """Return the list of fields for query"""
        raise NotImplementedError

    @classmethod
    def get_indexable(cls):
        # Some models have a gazillion instances. So we want to go
        # through them one at a time in a way that doesn't pull all
        # the data into memory all at once. So we iterate through ids
        # and pull objects one at a time.
        return cls.get_model().objects.order_by('id').values_list(
            'id', flat=True)

    @classmethod
    def index(cls, *args, **kwargs):
        if not settings.ES_LIVE_INDEXING:
            return

        super(SearchMappingType, cls).index(*args, **kwargs)

    @classmethod
    def unindex(cls, *args, **kwargs):
        if not settings.ES_LIVE_INDEXING:
            return

        try:
            super(SearchMappingType, cls).unindex(*args, **kwargs)
        except ElasticHttpNotFoundError:
            # Ignore the case where we try to delete something that's
            # not there.
            pass

    @classmethod
    def morelikethis(cls, id_, s, fields):
        """MoreLikeThis API"""
        return list(MLT(
                id_, s=s, mlt_fields=fields, min_term_freq=1, min_doc_freq=1))


_identity = lambda s: s


def register_for_indexing(app,
                          sender_class,
                          instance_to_indexee=_identity,
                          m2m=False):
    """Registers a model for signal-based live-indexing.

    As data changes in the database, we need to update the relevant
    documents in the index. This function registers Django model
    classes with the appropriate signals and update/delete routines
    such that our index stays up-to-date.

    :arg app: A bit of UID we use to build the signal handlers'
        dispatch_uids.  This is prepended to the ``sender_class``
        model name, "elastic", and the signal name, so it should
        combine with those to make something unique. For this reason,
        the app name is usually a good choice, yielding something like
        "wiki.TaggedItem.elastic.post_save".
    :arg sender_class: The class to listen for saves and deletes on.
    :arg instance_to_indexee: A callable which takes the signalling
        instance and returns the model instance to be indexed. The
        returned instance should be a subclass of SearchMixin. If the
        callable returns None, no indexing is performed.

        Default: a callable which returns the sender itself.
    :arg m2m: True if this is a m2m model and False otherwise.

    Examples::

        # Registers MyModel for indexing. post_save creates new
        # documents in the index. pre_delete removes documents
        # from the index.
        register_for_indexing(MyModel, 'some_app')

        # Registers RelatedModel for indexing. RelatedModel is related
        # to some model in the sense that the document in the index is
        # composed of data from some model and it's related
        # RelatedModel instance. Because of that when we update
        # RelatedModel instances, we need to update the associated
        # document in the index for the related model.
        #
        # This registers the RelatedModel for indexing. post_save and
        # pre_delete update the associated document in the index for
        # the related model. The related model instance is determined
        # by the instance_to_indexee function.
        register_for_indexing(RelatedModel, 'some_app',
                              instance_to_indexee=lambda r: r.my_model)


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

    if m2m:
        # This is an m2m model, so we regstier m2m_chaned and it
        # updates the existing document in the index.
        indexing_receiver(m2m_changed, 'm2m_changed')(update)

    else:
        indexing_receiver(post_save, 'post_save')(update)

        indexing_receiver(pre_delete, 'pre_delete')(
            # If it's the indexed instance that's been deleted, go ahead
            # and delete it from the index. Otherwise, we just want to
            # update whatever model it's related to.
            delete if instance_to_indexee is _identity else update)


def register_mapping_type(cls):
    """Class decorator for registering MappingTypes for search"""
    _search_mapping_types[cls.get_mapping_type_name()] = cls
    return cls


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
