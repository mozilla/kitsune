import json
import logging
import pprint
import time

from django.conf import settings
from django.db import reset_queries

from elasticutils.contrib.django import S, F, get_es, ES_EXCEPTIONS  # noqa
from pyelasticsearch.exceptions import ElasticHttpNotFoundError
from search.utils import chunked


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
CHUNK_SIZE = 20000


log = logging.getLogger('k.search.es')


class UnindexMeBro(Exception):
    """Raise in extract_document when doc should be removed."""
    pass


class SphilasticUnified(S):
    """Shim around elasticutils.contrib.django.S.

    Implements some Kitsune-specific behavior to make our lives
    easier.

    """
    def print_query(self):
        pprint.pprint(self._build_query())

    def get_indexes(self):
        # SphilasticUnified is a searcher and so it's _always_ used in
        # a read context. Therefore, we always return the READ_INDEX.
        return [READ_INDEX]

    def get_doctypes(self):
        # SUMO uses a unified doctype, so this always returns that.
        return [SUMO_DOCTYPE]

    def __repr__(self):
        return '<S %s>' % self._build_query()


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
    es = get_es()
    status = es.status()
    indexes = status['indices']

    if not all_indexes:
        indexes = dict((k, v) for k, v in indexes.items()
                       if k.startswith(settings.ES_INDEX_PREFIX))

    indexes = [(k, v['docs']['num_docs']) for k, v in indexes.items()]

    return indexes


def get_doctype_stats(index):
    """Returns a dict of name -> count for documents indexed.

    For example:

    >>> get_doctype_stats()
    {'questions_question': 14216, 'forums_thread': 419, 'wiki_document': 759}

    :throws pyelasticsearch.exceptions.Timeout: if the request
        times out
    :throws pyelasticsearch.exceptions.ConnectionError: if there's a
        connection error
    :throws pyelasticsearch.exceptions.ElasticHttpNotFound: if the
        index doesn't exist

    """
    from search.models import get_search_models

    s = SphilasticUnified(object)

    stats = {}
    for cls in get_search_models():
        model_name = cls.get_model_name()
        stats[model_name] = s.filter(model=model_name).count()

    return stats


def delete_index(index):
    try:
        get_es().delete_index(index)
    except ElasticHttpNotFoundError:
        pass


def format_time(time_to_go):
    """Returns minutes and seconds string for given time in seconds"""
    if time_to_go < 60:
        return "%ds" % time_to_go
    return "%dm %ds" % (time_to_go / 60, time_to_go % 60)


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
        es = get_es()

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


def get_indexable(percent=100, search_models=None):
    """Returns a list of (class, iterable) for all the things to index

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.
    :arg search_models: The list of models to index.

    """
    from search.models import get_search_models

    # Note: Passing in None will get all the models.
    search_models = get_search_models(search_models)

    to_index = []
    percent = float(percent) / 100
    for cls in search_models:
        indexable = cls.get_indexable()
        if percent < 1:
            indexable = indexable[:int(indexable.count() * percent)]
        to_index.append((cls, indexable))

    return to_index


def index_chunk(cls, id_list, reraise=False):
    """Index a chunk of documents.

    :arg cls: The MappingType class.
    :arg id_list: Iterable of ids of that MappingType to index.
    :arg reraise: False if you want errors to be swallowed and True
        if you want errors to be thrown.

    """
    # Note: This bulk indexes in batches of 80. I didn't arrive at
    # this number through a proper scientific method. It's possible
    # there's a better number. It takes a while to fiddle with,
    # though. Probably best to expose the number as an environment
    # variable, then run a script that takes timings for
    # --criticalmass, runs overnight and returns a more "optimal"
    # number.
    for ids in chunked(id_list, 80):
        documents = []
        for id_ in ids:
            try:
                documents.append(cls.extract_document(id_))

            except UnindexMeBro:
                # extract_document throws this in cases where we need
                # to remove the item from the index.
                cls.unindex(id_)

            except Exception:
                log.exception('Unable to extract/index document (id: %d)',
                              id_)
                if reraise:
                    raise

        if documents:
            cls.bulk_index(documents, id_field='document_id')


def es_reindex_cmd(percent=100, delete=False, models=None,
                   criticalmass=False, log=log):
    """Rebuild ElasticSearch indexes

    :arg percent: 1 to 100--the percentage of the db to index
    :arg delete: whether or not to wipe the index before reindexing
    :arg models: list of search model names to index
    :arg criticalmass: whether or not to index just a critical mass of
        things
    :arg log: the logger to use
    """
    es = get_es()

    try:
        get_doctype_stats(WRITE_INDEX)
    except ES_EXCEPTIONS:
        if not delete:
            log.error('The index does not exist. You must specify --delete.')
            return

    if delete:
        log.info('wiping and recreating %s....', WRITE_INDEX)
        recreate_index(es=es)

    if criticalmass:
        # The critical mass is defined as the entire KB plus the most
        # recent 15k questions (which is about how many questions
        # there were created in the last 180 days). We build that
        # indexable here.

        # Get only questions and wiki document stuff.
        all_indexable = get_indexable(
            search_models=['questions_question', 'wiki_document'])

        # The first item is questions because we specified that
        # order. Old questions don't show up in searches, so we nix
        # them by reversing the list (ordered by id ascending) and
        # slicing it.
        all_indexable[0] = (all_indexable[0][0],
                            list(reversed(all_indexable[0][1]))[:15000])

    elif models:
        all_indexable = get_indexable(percent, models)

    else:
        all_indexable = get_indexable(percent)

    log.info('using index: %s', WRITE_INDEX)

    start_time = time.time()
    for cls, indexable in all_indexable:
        cls_start_time = time.time()
        total = len(indexable)

        if total == 0:
            continue

        log.info('reindexing %s. %s to index....',
                 cls.get_model_name(), total)

        i = 0
        for chunk in chunked(indexable, 1000):
            chunk_start_time = time.time()
            index_chunk(cls, chunk)

            i += len(chunk)
            time_to_go = (total - i) * ((time.time() - cls_start_time) / i)
            per_1000 = (time.time() - cls_start_time) / (i / 1000.0)
            this_1000 = time.time() - chunk_start_time

            log.info('   %s/%s %s... (%s/1000 avg, %s ETA)',
                     i,
                     total,
                     format_time(this_1000),
                     format_time(per_1000),
                     format_time(time_to_go)
            )

            # We call this every 1000 or so because we're
            # essentially loading the whole db and if DEBUG=True,
            # then Django saves every sql statement which causes
            # our memory to go up up up. So we reset it and that
            # makes things happier even in DEBUG environments.
            reset_queries()

        delta_time = time.time() - cls_start_time
        log.info('   done! (%s total, %s/1000 avg)',
                 format_time(delta_time),
                 format_time(delta_time / (total / 1000.0)))

    delta_time = time.time() - start_time
    log.info('done! (%s total)', format_time(delta_time))


def es_delete_cmd(index, interactive=False, log=log):
    """Deletes an index"""
    try:
        indexes = [name for name, count in get_indexes()]
    except ES_EXCEPTIONS:
        log.error('Your elasticsearch process is not running or ES_URLS '
                  'is set wrong in your settings_local.py file.')
        return

    if index not in indexes:
        log.error('Index "%s" is not a valid index.', index)
        return

    if index == READ_INDEX and interactive:
        ret = raw_input('"%s" is a read index. Are you sure you want '
                        'to delete it? (yes/no) ' % index)
        if ret != 'yes':
            log.info('Not deleting the index.')
            return

    log.info('Deleting index "%s"...', index)
    delete_index(index)
    log.info('Done!')


def es_status_cmd(checkindex=False, log=log):
    """Shows elastic search index status"""
    try:
        read_doctype_stats = get_doctype_stats(READ_INDEX)
    except ES_EXCEPTIONS:
        read_doctype_stats = None

    if READ_INDEX == WRITE_INDEX:
        write_doctype_stats = read_doctype_stats
    else:
        try:
            write_doctype_stats = get_doctype_stats(WRITE_INDEX)
        except ES_EXCEPTIONS:
            write_doctype_stats = None

    try:
        indexes = get_indexes(all_indexes=True)
    except ES_EXCEPTIONS:
        log.error('Your elasticsearch process is not running or ES_URLS '
                  'is set wrong in your settings_local.py file.')
        return

    log.info('Settings:')
    log.info('  ES_URLS               : %s', settings.ES_URLS)
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


def es_search_cmd(query, pages=1, log=log):
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
        'q': query, 'format': 'json'
        }
    url = reverse('search')

    # The search view shows 10 results at a time. So we hit it few
    # times---once for each page.
    for pageno in range(pages):
        pageno = pageno + 1
        data['page'] = pageno
        resp = client.get(url, data)
        if resp.status_code != 200:
            output.append('ERROR: %s' % resp.content)
            break

        else:
            content = json.loads(resp.content)
            results = content[u'results']

            for mem in results:
                output.append(u'%4d  %5.2f  %-10s  %-20s' % (
                        mem['rank'], mem['score'], mem['type'], mem['title']))

            output.append('')

    for line in output:
        log.info(line.encode('ascii', 'ignore'))
