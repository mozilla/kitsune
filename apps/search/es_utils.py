from itertools import chain, count, izip
import logging
from pprint import pprint

import elasticutils
import pyes

from django.conf import settings


ESTimeoutError = pyes.urllib3.TimeoutError
ESMaxRetryError = pyes.urllib3.MaxRetryError
ESIndexMissingException = pyes.exceptions.IndexMissingException


log = logging.getLogger('search.es_utils')


def get_doctype_stats():
    """Returns a dict of name -> count for documents indexed.

    For example:

    >>> get_doctype_stats()
    {'questions_question': 14216, 'forums_thread': 419, 'wiki_document': 759}

    :throws pyes.urllib3.MaxRetryError: if it can't connect to elasticsearch
    :throws pyes.exceptions.IndexMissingException: if the index doesn't exist

    """
    from search.models import get_search_models

    stats = {}

    for cls in get_search_models():
        stats[cls._meta.db_table] = elasticutils.S(cls).count()

    return stats


def get_es(**kwargs):
    """Returns a fresh ES instance

    Defaults for these arguments come from settings. Specifying them
    in the function call will override the default.

    :arg server: settings.ES_HOSTS
    :arg timeout: settings.ES_INDEXING_TIMEOUT
    :arg bulk_size: settings.ES_FLUSH_BULK_EVERY

    """
    defaults = {
        'server': settings.ES_HOSTS,
        'timeout': settings.ES_INDEXING_TIMEOUT,
        'bulk_size': settings.ES_FLUSH_BULK_EVERY
        }
    defaults.update(kwargs)

    return pyes.ES(**defaults)


def format_time(time_to_go):
    """Returns minutes and seconds string for given time in seconds"""
    if time_to_go < 60:
        return "%ds" % time_to_go
    return  "%dm %ds" % (time_to_go / 60, time_to_go % 60)


def es_reindex_with_progress(doctypes=None, percent=100):
    """Rebuild Elastic indexes as you iterate over yielded progress ratios.

    :arg doctypes: Defaults to None which will index all doctypes.
        Otherwise indexes the doctypes specified. See
        :py:func:`.get_doctype_stats()` for what doctypes look like.
    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.

    """
    from search.models import get_search_models

    es = elasticutils.get_es()

    search_models = get_search_models()
    if doctypes:
        search_models = [cls for cls in search_models
                         if cls._meta.db_table in doctypes]

    if len(search_models) == len(get_search_models()):
        index = settings.ES_INDEXES.get('default')
        if index is not None:
            # If we're indexing everything and there's a default index
            # specified in settings, then we delete and recreate it.
            es.delete_index_if_exists(index)
            es.create_index(index)

    total = sum([cls.objects.count() for cls in search_models])

    to_index = [cls.index_all(percent) for cls in search_models]

    return (float(done) / total for done, _ in
            izip(count(1), chain(*to_index)))


def es_reindex(doctypes=None, percent=100):
    """Rebuild ElasticSearch indexes

    See :py:func:`.es_reindex_with_progress` for argument details.

    """
    [x for x in es_reindex_with_progress(doctypes, percent) if False]


def es_whazzup():
    """Runs cluster_stats on the Elastic system"""
    es = elasticutils.get_es()

    # TODO: It'd be better to show more useful information than raw
    # cluster_stats.
    try:
        pprint(es.cluster_stats())
    except pyes.urllib3.connectionpool.MaxRetryError:
        log.error('Your elasticsearch process is not running or ES_HOSTS '
                  'is set wrong in your settings_local.py file.')
        return

    log.info('Totals:')
    for name, count in get_doctype_stats().items():
        log.info(' * %s: %d', name, count)
