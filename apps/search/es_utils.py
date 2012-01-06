from itertools import chain, count, izip
import logging
from pprint import pprint
import time

import elasticutils
import pyes

from django.conf import settings


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


def reindex_model(cls, percent=100):
    """Reindexes all the objects for a single mode.

    Yields number of documents done.

    Note: This gets run from the command line, so we log stuff to let
    the user know what's going on.

    :arg cls: the model class
    :arg percent: The percentage of questions to index.  Defaults to
        100--e.g. all of them.

    """
    doc_type = cls._meta.db_table
    index = cls._get_index()

    start_time = time.time()

    log.info('reindex %s into %s index', doc_type, index)

    es = pyes.ES(settings.ES_HOSTS, timeout=settings.ES_INDEXING_TIMEOUT)

    log.info('setting up mapping....')
    mapping = cls.get_mapping()
    es.put_mapping(doc_type, mapping, index)

    log.info('iterating through %s....', doc_type)
    total = cls.objects.count()
    to_index = int(total * (percent / 100.0))
    log.info('total %s: %s (to be indexed: %s)', doc_type, total, to_index)
    total = to_index

    t = 0
    for obj in cls.objects.order_by('id').all():
        t += 1
        if t % 1000 == 0:
            time_to_go = (total - t) * ((time.time() - start_time) / t)
            if time_to_go < 60:
                time_to_go = "%d secs" % time_to_go
            else:
                time_to_go = "%d min" % (time_to_go / 60)
            log.info('%s/%s...  (%s to go)', t, total, time_to_go)

        if t % settings.ES_FLUSH_BULK_EVERY == 0:
            es.flush_bulk()

        if t > total:
            break

        cls.index(obj.extract_document(), bulk=True, es=es)
        yield t

    es.flush_bulk(forced=True)
    log.info('done!')
    es.refresh()


def es_reindex_with_progress(percent=100):
    """Rebuild Elastic indexes as you iterate over yielded progress ratios.

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.

    """
    from search.models import get_search_models

    es = elasticutils.get_es()

    # Go through and delete, then recreate the indexes.
    for index in settings.ES_INDEXES.values():
        es.delete_index_if_exists(index)
        es.create_index(index)

    search_models = get_search_models()

    total = sum([cls.objects.count() for cls in search_models])

    to_index = [reindex_model(cls, percent) for cls in search_models]

    return (float(done) / total for done, _ in
            izip(count(1), chain(*to_index)))


def es_reindex(percent=100):
    """Rebuild ElasticSearch indexes"""
    [x for x in es_reindex_with_progress(percent) if False]


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
