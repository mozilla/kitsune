from itertools import chain, count, izip
import logging

import elasticutils
import pyes

from django.conf import settings


ESTimeoutError = pyes.urllib3.TimeoutError
ESMaxRetryError = pyes.urllib3.MaxRetryError
ESIndexMissingException = pyes.exceptions.IndexMissingException


log = logging.getLogger('search.es_utils')


def get_indexes():
    es = get_indexing_es()
    indexes = [(k, v['num_docs']) for k, v in es.get_indices().items()
               if k.startswith(settings.ES_INDEX_PREFIX)]
    return indexes


def get_doctype_stats(index):
    """Returns a dict of name -> count for documents indexed.

    For example:

    >>> get_doctype_stats()
    {'questions_question': 14216, 'forums_thread': 419, 'wiki_document': 759}

    :throws pyes.urllib3.MaxRetryError: if it can't connect to elasticsearch
    :throws pyes.exceptions.IndexMissingException: if the index doesn't exist

    """
    from search.models import get_search_models

    es = elasticutils.get_es()
    query = pyes.query.MatchAllQuery()

    stats = {}

    for cls in get_search_models():
        stats[cls._meta.db_table] = es.count(
            query, indexes=[index], doc_types=[cls._meta.db_table])['count']

    return stats


def get_indexing_es(**kwargs):
    """Returns a fresh ES instance for indexing

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


def delete_index(index):
    elasticutils.get_es().delete_index_if_exists(index)


def format_time(time_to_go):
    """Returns minutes and seconds string for given time in seconds"""
    if time_to_go < 60:
        return "%ds" % time_to_go
    return  "%dm %ds" % (time_to_go / 60, time_to_go % 60)


def get_documents(cls, ids):
    """Returns a list of ES documents with specified ids and doctype"""
    es = elasticutils.get_es()
    doctype = cls._meta.db_table
    index = settings.ES_INDEXES['default']

    ret = es.search(pyes.query.IdsQuery(doctype, ids), indices=[index],
                    doc_types=[doctype])
    return ret['hits']['hits']


def es_reindex_with_progress(percent=100):
    """Rebuild Elastic indexes as you iterate over yielded progress ratios.

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.

    """
    from search.models import get_search_models

    search_models = get_search_models()

    es = elasticutils.get_es()
    index = settings.ES_WRITE_INDEXES['default']
    delete_index(index)

    # There should be no mapping-conflict race here since the index doesn't
    # exist. Live indexing should just fail.

    # Simultaneously create the index and the mappings, so live indexing
    # doesn't get a chance to index anything between the two and infer a bogus
    # mapping (which ES then freaks out over when we try to lay in an
    # incompatible explicit mapping).
    mappings = dict((cls._meta.db_table, {'properties': cls.get_mapping()})
                    for cls in search_models)
    es.create_index(index, settings={'mappings': mappings})

    total = sum([cls.get_indexable().count() for cls in search_models])
    to_index = [cls.index_all(percent) for cls in search_models]
    return (float(done) / total for done, _ in
            izip(count(1), chain(*to_index)))


def es_reindex_cmd(percent=100):
    """Rebuild ElasticSearch indexes

    See :py:func:`.es_reindex_with_progress` for argument details.

    """
    [x for x in es_reindex_with_progress(percent) if False]


def es_delete_cmd(index):
    """Deletes an index"""
    read_index = settings.ES_INDEXES['default']

    try:
        indexes = [name for name, count in get_indexes()]
    except ESMaxRetryError:
        log.error('Your elasticsearch process is not running or ES_HOSTS '
                  'is set wrong in your settings_local.py file.')
        return

    if index not in indexes:
        log.error('Index "%s" is not a valid index.', index)
        return

    if index == read_index:
        ret = raw_input('"%s" is a read index. Are you sure you want '
                        'to delete it? (yes/no) ' % index)
        if ret != 'yes':
            return

    log.info('Deleting index "%s"...', index)
    delete_index(index)
    log.info('Done!')


def es_status_cmd():
    """Shows elastic search index status"""
    read_index = settings.ES_INDEXES['default']
    write_index = settings.ES_WRITE_INDEXES['default']

    try:
        try:
            read_doctype_stats = get_doctype_stats(read_index)
        except ESIndexMissingException:
            read_doctype_stats = None
        try:
            write_doctype_stats = get_doctype_stats(write_index)
        except ESIndexMissingException:
            write_doctype_stats = None
        indexes = get_indexes()
    except ESMaxRetryError:
        log.error('Your elasticsearch process is not running or ES_HOSTS '
                  'is set wrong in your settings_local.py file.')
        return

    log.info('Settings:')
    log.info('  ES_HOSTS              : %s', settings.ES_HOSTS)
    log.info('  ES_INDEX_PREFIX       : %s', settings.ES_INDEX_PREFIX)
    log.info('  ES_LIVE_INDEXING      : %s', settings.ES_LIVE_INDEXING)
    log.info('  ES_INDEXES            : %s', settings.ES_INDEXES)
    log.info('  ES_WRITE_INDEXES      : %s', settings.ES_WRITE_INDEXES)

    log.info('Index stats:')

    if indexes:
        log.info('  List of %s indexes:', settings.ES_INDEX_PREFIX)
        for name, count in indexes:
            read_write = []
            if name == read_index:
                read_write.append('READ')
            if name == write_index:
                read_write.append('WRITE')
            log.info('    %-20s: %s %s', name, count,
                     '/'.join(read_write))
    else:
        log.info('  There are no %s indexes.', settings.ES_INDEX_PREFIX)

    if read_doctype_stats is None:
        log.info('  Read index does not exist. (%s)', read_index)
    else:
        log.info('  Read index (%s):', read_index)
        for name, count in read_doctype_stats.items():
            log.info('    %-20s: %d', name, count)

    if read_index != write_index:
        if write_doctype_stats is None:
            log.info('  Write index does not exist. (%s)', write_index)
        else:
            log.info('  Write index (%s):', write_index)
            for name, count in write_doctype_stats.items():
                log.info('    %-20s: %d', name, count)
    else:
        log.info('  Write index is same as read index.')
