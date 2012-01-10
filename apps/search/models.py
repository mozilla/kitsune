import elasticutils
import logging
import pyes
from threading import local

from django.conf import settings
from django.core import signals

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
    @classmethod
    def register_search_model(cls):
        """Registers a model as being involved with ES indexing"""
        # TODO: Fix this to use weakrefs
        _search_models[cls._meta.db_table] = cls

    def extract_document(self):
        """Extracts the ES index document for this instance"""
        return {}

    @classmethod
    def _get_index(cls):
        """Returns the index for this class"""
        indexes = settings.ES_INDEXES
        return indexes.get(cls._meta.db_table) or indexes['default']

    @classmethod
    def add_index_task(cls, ids):
        """Adds an index task.

        :arg args: tuple of ids

        """
        _local_tasks.es_index_task_set.add((index_task, (cls, ids)))

    @classmethod
    def add_unindex_task(cls, ids):
        """Creates a task to remove this document from the ES index

        :arg args: tuple of ids

        """
        _local_tasks.es_index_task_set.add((unindex_task, (cls, ids)))

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
