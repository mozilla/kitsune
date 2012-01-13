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
    """Returns a fresh ES instance with specified arguments"""
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


def reindex_model(cls, percent=100):
    """Reindexes all the objects for a single mode.

    Yields number of documents done.

    Note: This gets run from the command line, so we log stuff to let
    the user know what's going on.

    :arg cls: the model class
    :arg percent: The percentage of questions to index.  Defaults to
        100--e.g. all of them.

    """
    es = get_es()

    doc_type = cls._meta.db_table
    index = cls.get_es_index()

    if index != settings.ES_INDEXES.get('default'):
        # If this doctype isn't using the default index, then this
        # doctype is responsible for deleting and re-creating the
        # index.
        es.delete_index_if_exists(index)
        es.create_index(index)

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

    t = 0

    # TODO: Doing values_list here instead of getting all the objects
    # results in a dramatic decrease in memory usage during indexing
    # to the point where my system with 4gb of memory can't get
    # through a full indexing without this "fix".
    for obj_id in cls.objects.order_by('id').values_list('id', flat=True):
        obj = cls.objects.get(pk=obj_id)
        t += 1
        if t > total:
            break

        if t % 1000 == 0:
            time_to_go = (total - t) * ((time.time() - start_time) / t)
            log.info('%s/%s...  (%s to go)', t, total, format_time(time_to_go))

        if t % settings.ES_FLUSH_BULK_EVERY == 0:
            es.flush_bulk()

        try:
            doc = obj.extract_document()
            del obj
            cls.index(doc, bulk=True, es=es)
            del doc
        except Exception:
            log.exception('Unable to extract document (id: %d)', obj_id)

        yield t

    es.flush_bulk(forced=True)
    end_time = time.time()
    log.info('done!  (%s)', format_time(end_time - start_time))
    es.refresh()


def es_reindex_with_progress(doctypes=None, percent=100):
    """Rebuild Elastic indexes as you iterate over yielded progress ratios.

    :arg doctypes: Defaults to None which will index all doctypes.
        Otherwise indexes the doctypes specified.
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

    to_index = [reindex_model(cls, percent) for cls in search_models]

    return (float(done) / total for done, _ in
            izip(count(1), chain(*to_index)))


def es_reindex(*args, **kwargs):
    """Rebuild ElasticSearch indexes"""
    [x for x in es_reindex_with_progress(*args, **kwargs) if False]


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
