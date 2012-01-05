from itertools import chain, count, izip
import logging
from threading import local

import elasticutils
from pprint import pprint
import pyes

from django.conf import settings
from django.core import signals


ESTimeoutError = pyes.urllib3.TimeoutError
ESMaxRetryError = pyes.urllib3.MaxRetryError
ESIndexMissingException = pyes.exceptions.IndexMissingException


TYPE = 'type'
ANALYZER = 'analyzer'
INDEX = 'index'
STORE = 'store'
TERM_VECTOR = 'term_vector'

NOT_INDEXED = 'not_indexed'

LONG = 'long'
INTEGER = 'integer'
STRING = 'string'
BOOLEAN = 'boolean'
DATE = 'date'

ANALYZED = 'analyzed'
NOTANALYZED = 'not_analyzed'

SNOWBALL = 'snowball'

YES = 'yes'

WITH_POS_OFFSETS = 'with_positions_offsets'


_thread_local = local()
_thread_local.es_index_task_set = set()


def add_index_task(fun, *args):
    """Adds an index task.

    Note: args and its contents **must** be hashable.

    :arg fun: the function to call
    :arg args: arguments to the function

    """
    _thread_local.es_index_task_set.add((fun, args))


def generate_tasks(**kwargs):
    """Goes through thread local index update tasks set and generates
    celery tasks for all tasks in the set.

    Because this works off of a set, it naturally de-dupes the tasks,
    so if four tasks get tossed into the set that are identical, we
    execute it only once.

    """
    if not _thread_local.es_index_task_set:
        return

    for fun, args in _thread_local.es_index_task_set:
        fun(*args)

    _thread_local.es_index_task_set.clear()


signals.request_finished.connect(generate_tasks)


def get_index(model):
    """Returns the index name for this model."""
    return (settings.ES_INDEXES.get(model._meta.db_table)
            or settings.ES_INDEXES['default'])


def get_doctype_stats():
    """Returns a dict of name -> count for documents indexed.

    For example:

    >>> get_doctype_stats()
    {'questions': 1000, 'forums': 1000, 'wiki': 1000}

    :throws pyes.urllib3.MaxRetryError: if it can't connect to elasticsearch
    :throws pyes.exceptions.IndexMissingException: if the index doesn't exist
    """
    # TODO: We have to import these here, otherwise we have an import
    # loop es_utils -> models.py -> es_utils. This should get fixed by
    # having the models register themselves as indexable with es_utils
    # or something like that. Then es_utils won't have to explicitly
    # know about models.
    from forums.models import Thread
    from questions.models import Question
    from wiki.models import Document

    stats = {}

    for name, model in (('questions', Question),
                        ('forums', Thread),
                        ('wiki', Document)):
        stats[name] = elasticutils.S(model).count()

    return stats


def es_reindex_with_progress(percent=100):
    """Rebuild Elastic indexes as you iterate over yielded progress ratios.

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.

    """
    # TODO: We have to import these here, otherwise we have an import
    # loop es_utils -> models.py -> es_utils. This should get fixed by
    # having the models register themselves as indexable with es_utils
    # or something like that. Then es_utils won't have to explicitly
    # know about models.
    import forums.es_search
    from forums.models import Thread
    import questions.es_search
    from questions.models import Question
    import wiki.es_search
    from wiki.models import Document

    es = elasticutils.get_es()

    # Go through and delete, then recreate the indexes.
    for index in settings.ES_INDEXES.values():
        es.delete_index_if_exists(index)
        es.create_index_if_missing(index)  # Should always be missing.

    # TODO: Having the knowledge of apps' internals repeated here is lame.
    total = (Question.objects.count() +
             Thread.objects.count() +
             Document.objects.count())
    return (float(done) / total for done, _ in
            izip(count(1),
                 chain(questions.es_search.reindex_questions(percent),
                       wiki.es_search.reindex_documents(percent),
                       forums.es_search.reindex_documents(percent))))


def es_reindex(percent=100):
    """Rebuild ElasticSearch indexes."""
    [x for x in es_reindex_with_progress(percent) if False]


def es_whazzup():
    """Runs cluster_stats on the Elastic system."""
    # We create a logger because elasticutils uses it.
    logging.basicConfig()

    es = elasticutils.get_es()

    try:
        pprint(es.cluster_stats())
    except pyes.urllib3.connectionpool.MaxRetryError:
        print ('ERROR: Your elasticsearch process is not running or '
               'ES_HOSTS is set wrong in your settings_local.py file.')
        return

    print 'Totals:'
    for name, count in get_doctype_stats().items():
        print '* %s: %d' % (name, count)
