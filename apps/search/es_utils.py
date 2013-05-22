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


class MappingMergeError(Exception):
    """Represents a mapping merge error"""
    pass


class UnindexMeBro(Exception):
    """Raise in extract_document when doc should be removed."""
    pass


class Sphilastic(S):
    """Shim around elasticutils.contrib.django.S.

    Implements some Kitsune-specific behavior to make our lives
    easier.

    .. Note::

       This looks at the READ_INDEX. If you need to look at something
       different, build your own S.

    """
    def print_query(self):
        pprint.pprint(self._build_query())

    def get_indexes(self):
        # SphilasticUnified is a searcher and so it's _always_ used in
        # a read context. Therefore, we always return the READ_INDEX.
        return [READ_INDEX]

    def process_query_mlt(self, key, val, action):
        """Add support for a more like this query to our S.

        val is expected to be a dict like:
            {
                'fields': ['field1', 'field2'],
                'like_text': 'text like this one',
            }
        """
        return {
            'more_like_this': val,
        }


def get_mappings():
    mappings = {}

    from search.models import get_mapping_types
    for cls in get_mapping_types():
        mappings[cls.get_mapping_type_name()] = cls.get_mapping()

    return mappings


def get_indexes(all_indexes=False):
    es = get_es()
    status = es.status()
    indexes = status['indices']

    if not all_indexes:
        indexes = dict((k, v) for k, v in indexes.items()
                       if k.startswith(settings.ES_INDEX_PREFIX))

    return [(name, value['docs']['num_docs'])
            for name, value in indexes.items()]


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
    stats = {}

    from search.models import get_mapping_types
    for cls in get_mapping_types():
        stats[cls.get_mapping_type_name()] = cls.search().count()

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

    :returns: list of documents as dicts
    """
    ret = cls.search().filter(id__in=ids).values_dict()[:len(ids)]
    return list(ret)


def recreate_index(es=None):
    """Deletes WRITE_INDEX if it's there and creates a new one"""
    if es is None:
        es = get_es()

    index = WRITE_INDEX
    delete_index(index)

    mappings = get_mappings()

    # There should be no mapping-conflict race here since the index doesn't
    # exist. Live indexing should just fail.

    # Simultaneously create the index and the mappings, so live
    # indexing doesn't get a chance to index anything between the two
    # and infer a bogus mapping (which ES then freaks out over when we
    # try to lay in an incompatible explicit mapping).
    es.create_index(index, settings={'mappings': mappings})

    # Wait until the index is there.
    es.health(wait_for_status='yellow')


def get_index_settings(index):
    """Returns ES settings for this index"""
    es = get_es()
    return es.get_settings(index).get(index, {}).get('settings', {})


def get_indexable(percent=100, mapping_types=None):
    """Returns a list of (class, iterable) for all the things to index

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.
    :arg mapping_types: The list of mapping types to index.

    """
    from search.models import get_mapping_types

    # Note: Passing in None will get all the mapping types
    mapping_types = get_mapping_types(mapping_types)

    to_index = []
    percent = float(percent) / 100
    for cls in mapping_types:
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
            cls.bulk_index(documents, id_field='id')

        if settings.DEBUG:
            # Nix queries so that this doesn't become a complete
            # memory hog and make Will's computer sad when DEBUG=True.
            reset_queries()


def es_reindex_cmd(percent=100, delete=False, mapping_types=None,
                   criticalmass=False, log=log):
    """Rebuild ElasticSearch indexes

    :arg percent: 1 to 100--the percentage of the db to index
    :arg delete: whether or not to wipe the index before reindexing
    :arg mapping_types: list of mapping types to index
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
            mapping_types=['questions_question', 'wiki_document'])

        # The first item is questions because we specified that
        # order. Old questions don't show up in searches, so we nix
        # them by reversing the list (ordered by id ascending) and
        # slicing it.
        all_indexable[0] = (all_indexable[0][0],
                            list(reversed(all_indexable[0][1]))[:15000])

    elif mapping_types:
        all_indexable = get_indexable(percent, mapping_types)

    else:
        all_indexable = get_indexable(percent)

    # We're doing a lot of indexing, so we get the refresh_interval
    # currently in the index, then nix refreshing. Later we'll restore
    # it.
    old_refresh = get_index_settings(WRITE_INDEX).get(
        'index.refresh_interval', '1s')

    # Disable automatic refreshing
    es.update_settings(
        WRITE_INDEX, {'index': {'refresh_interval': '-1'}})

    log.info('using index: %s', WRITE_INDEX)

    start_time = time.time()
    for cls, indexable in all_indexable:
        cls_start_time = time.time()
        total = len(indexable)

        if total == 0:
            continue

        log.info('reindexing %s. %s to index....',
                 cls.get_mapping_type_name(), total)

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

        delta_time = time.time() - cls_start_time
        log.info('   done! (%s total, %s/1000 avg)',
                 format_time(delta_time),
                 format_time(delta_time / (total / 1000.0)))

    # Re-enable automatic refreshing
    es.update_settings(
        WRITE_INDEX, {'index': {'refresh_interval': old_refresh}})
    delta_time = time.time() - start_time
    log.info('done! (%s total)', format_time(delta_time))


def es_delete_cmd(index, noinput=False, log=log):
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

    if index == READ_INDEX and not noinput:
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
    log.info('  ES_URLS                 : %s', settings.ES_URLS)
    log.info('  ES_INDEX_PREFIX         : %s', settings.ES_INDEX_PREFIX)
    log.info('  ES_LIVE_INDEXING        : %s', settings.ES_LIVE_INDEXING)
    log.info('  ES_INDEXES              : %s', settings.ES_INDEXES)
    log.info('  ES_WRITE_INDEXES        : %s', settings.ES_WRITE_INDEXES)

    log.info('Index stats:')

    if indexes:
        log.info('  List of indexes:')
        for name, count in sorted(indexes):
            read_write = []
            if name == READ_INDEX:
                read_write.append('READ')
            if name == WRITE_INDEX:
                read_write.append('WRITE')
            log.info('    %-22s: %s %s', name, count,
                     '/'.join(read_write))
    else:
        log.info('  There are no %s indexes.', settings.ES_INDEX_PREFIX)

    if read_doctype_stats is None:
        log.info('  Read index does not exist. (%s)', READ_INDEX)
    else:
        log.info('  Read index (%s):', READ_INDEX)
        for name, count in sorted(read_doctype_stats.items()):
            log.info('    %-22s: %d', name, count)

    if READ_INDEX != WRITE_INDEX:
        if write_doctype_stats is None:
            log.info('  Write index does not exist. (%s)', WRITE_INDEX)
        else:
            log.info('  Write index (%s):', WRITE_INDEX)
            for name, count in sorted(write_doctype_stats.items()):
                log.info('    %-22s: %d', name, count)
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


def es_verify_cmd(log=log):
    log.info('Behold! I am the magificent esverify command and I shall verify')
    log.info('all things verifyable so that you can rest assured that your')
    log.info('changes are bereft of the tawdry clutches of whimsy and')
    log.info('misfortune.')
    log.info('')

    mappings = get_mappings()

    log.info('Verifying mappings do not conflict.')

    # Verify mappings don't conflict
    merged_mapping = {}

    start_time = time.time()
    for cls_name, mapping in mappings.items():
        mapping = mapping['properties']
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

    log.info('Done! {0}'.format(format_time(time.time() - start_time)))
    log.info('')

    log.info('Verifying all documents are correctly typed.')

    # Note: This is some goofy type coercion between ES and Python
    # types and Python type behavior
    type_map = {
        'string': basestring,
        'integer': (int, long),
        'long': (int, long),
        'boolean': bool
    }

    def verify_obj(mt_name, cls, mapping, obj_id):
        try:
            doc = cls.extract_document(obj_id=obj_id)
        except UnindexMeBro:
            return

        for field, type_ in mapping.items():
            python_type = type_map[type_['type']]
            item = doc.get(field)

            if item is None or isinstance(item, python_type):
                continue

            if isinstance(item, (tuple, list)):
                for mem in item:
                    if not isinstance(mem, python_type):
                        log.error('   bad type: {0} {1} {2} {3}'.format(
                                mt_name, field, type_['type'], item))
                continue

            log.error('   bad type: {0} {1} {2} {3}'.format(
                    mt_name, field, type_['type'], item))

    start_time = time.time()

    log.info('MappingType indexable.')
    for cls, indexable in get_indexable():
        count = 0
        cls_time = time.time()

        mt_name = cls.get_mapping_type_name()
        mapping = mappings[mt_name]
        if 'properties' in mapping:
            mapping = mapping['properties']

        log.info('   Working on {0}'.format(mt_name))
        for obj in indexable:
            verify_obj(mt_name, cls, mapping, obj)

            count += 1
            if count % 1000 == 0:
                log.info('      {0} ({1}/1000 avg)'.format(
                        count,
                        format_time((time.time() - cls_time) * 1000 / count)))

                if settings.DEBUG:
                    # Nix queries so that this doesn't become a complete
                    # memory hog and make Will's computer sad when DEBUG=True.
                    reset_queries()

        log.info('      Done! {0} ({1}/1000 avg)'.format(
                format_time(time.time() - cls_time),
                format_time((time.time() - cls_time) * 1000 / count)))

    log.info('Done! {0}'.format(format_time(time.time() - start_time)))
