import json
import logging
from itertools import chain, count, izip

from django.conf import settings

import elasticutils
import pyes


ESTimeoutError = pyes.urllib3.TimeoutError
ESMaxRetryError = pyes.urllib3.MaxRetryError
ESIndexMissingException = pyes.exceptions.IndexMissingException
ESException = pyes.exceptions.ElasticSearchException


# Calculate index names.
#
# Note: This means that you need to restart kitsune to pick up new
# index names. If that turns out to be lame, then we should switch
# these to be functions.
READ_INDEX = (u'%s_%s' % (settings.ES_INDEX_PREFIX,
                          settings.ES_INDEXES['default']))

WRITE_INDEX = (u'%s_%s' % (settings.ES_INDEX_PREFIX,
                           settings.ES_WRITE_INDEXES['default']))


log = logging.getLogger('search.es_utils')


class Sphilastic(elasticutils.S):
    """Shim around elasticutils' S which makes it look like oedipus.S

    It ignores or implements workalikes for our Sphinx-specific API
    deviations.

    Use this when you're using ElasticSearch if your project is flipping
    quickly between ElasticSearch and Sphinx.

    .. Note::

       Originally taken from oedipus and put here so I can stop
       touching oedipus when I need to make changes.

    """
    def get_index(self):
        # Sphilastic is a searcher and so it's _always_ used in a read
        # context. Therefore, we always return the READ_INDEX.
        return READ_INDEX

    def query(self, text, **kwargs):
        """Ignore any non-kw arg."""
        # TODO: If you're feeling fancy, turn the `text` arg into an "or"
        # query across all fields, or use the all_ index, or something.
        return super(Sphilastic, self).query(text, **kwargs)

    def object_ids(self):
        """Returns a list of object IDs from Sphinx matches.

        If there's a ``SphinxMeta.id_field``, then this will be the
        values of that field in the results set.  Otherwise it's the
        ids in the results set.

        """
        # We don't want object_ids() to bring back highlighted
        # stuff ("Just the ids, ma'am."), so we gimp
        # _build_highlight to do nothing, then do our self.raw(),
        # then ungimp it. That prevents highlight-related bits
        # from showing up in the query and results.

        build_highlight = self._build_highlight
        self._build_highlight = lambda: {}

        hits = self.raw()['hits']['hits']

        self._build_highlight = build_highlight

        return [int(r['_id']) for r in hits]

    def order_by(self, *fields):
        """Change @rank to _score, which ES understands."""
        transforms = {'@rank': '_score',
                      '-@rank': '-_score'}
        return super(Sphilastic, self).order_by(
            *[transforms.get(f, f) for f in fields])

    def group_by(self, *args, **kwargs):
        """Do nothing.

        In ES, we smoosh subentities into their parents and index them
        as a single document, so making this a nop works out.

        """
        return self


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
    index = READ_INDEX

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
    index = WRITE_INDEX
    delete_index(index)

    # There should be no mapping-conflict race here since the index doesn't
    # exist. Live indexing should just fail.

    # Simultaneously create the index and the mappings, so live
    # indexing doesn't get a chance to index anything between the two
    # and infer a bogus mapping (which ES then freaks out over when we
    # try to lay in an incompatible explicit mapping).
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
    try:
        indexes = [name for name, count in get_indexes()]
    except ESMaxRetryError:
        log.error('Your elasticsearch process is not running or ES_HOSTS '
                  'is set wrong in your settings_local.py file.')
        return

    if index not in indexes:
        log.error('Index "%s" is not a valid index.', index)
        return

    if index == READ_INDEX:
        ret = raw_input('"%s" is a read index. Are you sure you want '
                        'to delete it? (yes/no) ' % index)
        if ret != 'yes':
            return

    log.info('Deleting index "%s"...', index)
    delete_index(index)
    log.info('Done!')


def es_status_cmd():
    """Shows elastic search index status"""
    try:
        try:
            read_doctype_stats = get_doctype_stats(READ_INDEX)
        except ESIndexMissingException:
            read_doctype_stats = None
        try:
            write_doctype_stats = get_doctype_stats(WRITE_INDEX)
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
            if name == READ_INDEX:
                read_write.append('READ')
            if name == WRITE_INDEX:
                read_write.append('WRITE')
            log.info('    %-20s: %s %s', name, count,
                     '/'.join(read_write))
    else:
        log.info('  There are no %s indexes.', settings.ES_INDEX_PREFIX)

    if read_doctype_stats is None:
        log.info('  Read index does not exist. (%s)', READ_INDEX)
    else:
        log.info('  Read index (%s):', READ_INDEX)
        for name, count in read_doctype_stats.items():
            log.info('    %-20s: %d', name, count)

    if READ_INDEX != WRITE_INDEX:
        if write_doctype_stats is None:
            log.info('  Write index does not exist. (%s)', WRITE_INDEX)
        else:
            log.info('  Write index (%s):', WRITE_INDEX)
            for name, count in write_doctype_stats.items():
                log.info('    %-20s: %d', name, count)
    else:
        log.info('  Write index is same as read index.')


def es_search_cmd(query):
    """Simulates a front page search

    .. Note::

       This **doesn't** simulate an advanced search---just a front
       page search.

    """
    from sumo.tests import LocalizingClient
    from sumo.urlresolvers import reverse

    client = LocalizingClient()

    output = []
    output.append('Search for: %s' % query)
    output.append('')

    data = {
        'q': query,
        'q_tags': 'desktop', 'product': 'desktop', 'format': 'json'
        }
    url = reverse('search')

    # The search view shows 10 results at a time. So we hit it few
    # times---once for each page.
    for pageno in ('1', '2', '3'):
        data['page'] = pageno
        resp = client.get(url, data)
        assert resp.status_code == 200

        content = json.loads(resp.content)
        results = content[u'results']

        for mem in results:
            output.append(u'%4d  %5.2f  %-10s  %-20s' % (
                    mem['rank'], mem['score'], mem['type'], mem['title']))

        output.append('')

    print '\n'.join(output)
