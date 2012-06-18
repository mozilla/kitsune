import json
import logging
import pprint
import time

from django.conf import settings
from django.db import reset_queries

import elasticutils
import pyes

from search.utils import chunked


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

# This is the unified elastic search doctype.
SUMO_DOCTYPE = u'sumodoc'

# The number of things in a chunk. This is for parallel indexing via
# the admin.
CHUNK_SIZE = 50000


log = logging.getLogger('search.es')


F = elasticutils.F


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
    _query_fields = []

    def _clone(self, next_step=None):
        new = super(Sphilastic, self)._clone(next_step)
        new._query_fields = list(self._query_fields)
        return new

    def print_query(self):
        pprint.pprint(self._build_query())

    def get_index(self):
        # Sphilastic is a searcher and so it's _always_ used in a read
        # context. Therefore, we always return the READ_INDEX.
        return READ_INDEX

    def get_doctype(self):
        # SUMO uses a unified doctype, so this always returns that.
        return SUMO_DOCTYPE

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

    def query_fields(self, *fields):
        new = self._clone()
        new._query_fields = fields
        return new

    def query(self, *args, **kws):
        """Sets up a query

        You can specify the query one of two ways:

        1. Call query_fields() with the fields you want to query
           BEFORE you call query. Then query will run that query
           with the specified fields.

           Example::

               S(Foo).query_fields('content__text', 'title__text', 'author')
                     .query('tabs')

           Note that we only search one value at a time.

        2. Call query with keyword arguments. This works just like in
           elasticutils documentation.

           Example::

               S(Foo).query(or_=dict(content__text='tabs',
                                     title__text='tabs',
                                     author='tabs'))

        """
        assert bool(args) != bool(kws)
        if args:
            # Note: We only look at the first arg. The rest we ignore.
            kws = dict(or_=dict(
                    (field, args[0]) for field in self._query_fields))
        return super(Sphilastic, self).query(**kws)


class MappingMergeError(Exception):
    """Represents a mapping merge error"""
    pass


def merge_mappings(mappings):
    merged_mapping = {}

    for cls_name, mapping in mappings:
        for key, val in mapping.items():
            if key not in merged_mapping:
                merged_mapping[key] = (val, [cls_name])
                continue

            # FIXME - We're comparing two dicts here. This might not
            # work for non-trivial dicts.
            if merged_mapping[key][0] != val:
                raise MappingMergeError(
                    '%s key different for %s and %s' %
                    (key, cls_name, merged_mapping[key][1]))

            merged_mapping[key][1].append(cls_name)

    # Remove cls_name annotations from final mapping
    merged_mapping = dict(
        [(key, val[0]) for key, val in merged_mapping.items()])
    return merged_mapping


def get_indexes(all_indexes=False):
    es = get_indexing_es()
    if all_indexes:
        indexes = [(k, v['num_docs']) for k, v in es.get_indices().items()]
    else:
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

    conn = elasticutils.get_es()

    stats = {}
    for cls in get_search_models():
        query = pyes.query.TermQuery('model', cls.get_model_name())
        results = conn.count(query=query, indexes=[index],
                             doc_types=[SUMO_DOCTYPE])
        stats[cls.get_model_name()] = results[u'count']

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
    """Returns a list of ES documents with specified ids and doctype

    :arg cls: the class with a ``.search()`` to use
    :arg ids: the list of ids to retrieve documents for
    """
    ret = cls.search().filter(id__in=ids).values_dict()[:len(ids)]
    return list(ret)


def recreate_index(es=None):
    """Deletes index if it's there and creates a new one"""
    if es is None:
        es = elasticutils.get_es()

    from search.models import get_search_models

    search_models = get_search_models()
    merged_mapping = {
        SUMO_DOCTYPE: {
            'properties': merge_mappings(
                [(cls._meta.db_table, cls.get_mapping())
                 for cls in search_models])
            }
        }

    index = WRITE_INDEX
    delete_index(index)

    # There should be no mapping-conflict race here since the index doesn't
    # exist. Live indexing should just fail.

    # Simultaneously create the index and the mappings, so live
    # indexing doesn't get a chance to index anything between the two
    # and infer a bogus mapping (which ES then freaks out over when we
    # try to lay in an incompatible explicit mapping).

    es.create_index(index, settings={'mappings': merged_mapping})


def get_indexable(percent=100):
    """Returns a list of (class, iterable) for all the things to index

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.

    """
    from search.models import get_search_models

    search_models = get_search_models()
    to_index = []
    percent = float(percent) / 100
    for cls in search_models:
        indexable = cls.get_indexable()
        if percent < 1:
            indexable = indexable[:int(indexable.count() * percent)]
        to_index.append((cls, indexable))

    return to_index


def index_chunk(cls, chunk, reraise=False, es=None):
    if es is None:
        es = get_indexing_es()

    try:
        for id_ in chunk:
            try:
                cls.index(cls.extract_document(id_), bulk=True, es=es)
            except Exception:
                log.exception('Unable to extract/index document (id: %d)', id_)
                if reraise:
                    raise

    finally:
        # Try to do these things, but if we fail, it's probably the case
        # that many things are broken, so just move on.
        try:
            es.flush_bulk(forced=True)
            es.refresh(WRITE_INDEX, timesleep=0)
        except Exception:
            log.exception('Unable to flush/refresh')


def es_reindex_cmd(percent=100, delete=False):
    """Rebuild ElasticSearch indexes

    :arg percent: 1 to 100--the percentage of the db to index
    :arg delete: whether or not to wipe the index before reindexing

    """
    es = get_indexing_es()

    try:
        get_doctype_stats(WRITE_INDEX)
    except ESIndexMissingException:
        if not delete:
            log.error('The index does not exist. You must specify --delete.')
            return

    if delete:
        log.info('wiping and recreating %s....', WRITE_INDEX)
        recreate_index(es=es)

    start_time = time.time()

    for cls, indexable in get_indexable(percent):
        cls_start_time = time.time()
        total = len(indexable)

        if total == 0:
            continue

        log.info('reindex %s into %s index. %s to index....',
                 cls.get_model_name(),
                 WRITE_INDEX, total)

        i = 0
        for chunk in chunked(indexable, 1000):
            index_chunk(cls, chunk, es=es)

            i += len(chunk)
            time_to_go = (total - i) * ((time.time() - start_time) / i)
            per_1000 = (time.time() - start_time) / (i / 1000.0)
            log.info('%s/%s... (%s to go, %s per 1000 docs)', i, total,
                     format_time(time_to_go),
                     format_time(per_1000))

            # We call this every 1000 or so because we're
            # essentially loading the whole db and if DEBUG=True,
            # then Django saves every sql statement which causes
            # our memory to go up up up. So we reset it and that
            # makes things happier even in DEBUG environments.
            reset_queries()

        delta_time = time.time() - cls_start_time
        log.info('done! (%s, %s per 1000 docs)',
                 format_time(delta_time),
                 format_time(delta_time / (total / 1000.0)))

    delta_time = time.time() - start_time
    log.info('done! (total time: %s)', format_time(delta_time))


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


def es_status_cmd(checkindex=False):
    """Shows elastic search index status"""
    try:
        try:
            read_doctype_stats = get_doctype_stats(READ_INDEX)
        except ESIndexMissingException:
            read_doctype_stats = None

        if READ_INDEX == WRITE_INDEX:
            write_doctype_stats = read_doctype_stats
        else:
            try:
                write_doctype_stats = get_doctype_stats(WRITE_INDEX)
            except ESIndexMissingException:
                write_doctype_stats = None

        indexes = get_indexes(all_indexes=True)
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
        log.info('  List of indexes:')
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

    if checkindex:
        # Go through the index and verify everything
        log.info('Checking index contents....')

        missing_docs = 0

        for cls, id_list in get_indexable():
            for id_group in chunked(id_list, 100):
                doc_list = get_documents(cls, id_group)
                if len(id_group) != len(doc_list):
                    doc_list_ids = [doc['id'] for doc in doc_list]
                    for id_ in id_group:
                        if id_ not in doc_list_ids:
                            log.info('   Missing %s %s',
                                     cls.get_model_name(), id_)
                            missing_docs += 1

        if missing_docs:
            print 'There were %d missing_docs' % missing_docs


def es_search_cmd(query, pages=1):
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
    for pageno in range(pages):
        pageno = pageno + 1
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
