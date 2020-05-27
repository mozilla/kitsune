import json
import logging
import pprint
import time
from functools import wraps

from django.conf import settings
from django.db import reset_queries
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

import requests
from elasticutils import S as UntypedS
from elasticutils.contrib.django import S, F, get_es, ES_EXCEPTIONS  # noqa

from kitsune.search import config
from kitsune.search.utils import chunked


# These used to be constants, but that was problematic. Things like
# tests want to be able to dynamically change settings at run time,
# which isn't possible if these are constants.

def read_index(group):
    """Gets the name of the read index for a group."""
    return ('%s_%s' % (settings.ES_INDEX_PREFIX,
                        settings.ES_INDEXES[group]))


def write_index(group):
    """Gets the name of the write index for a group."""
    return ('%s_%s' % (settings.ES_INDEX_PREFIX,
                        settings.ES_WRITE_INDEXES[group]))


def all_read_indexes():
    return [read_index(group) for group in list(settings.ES_INDEXES.keys())]


def all_write_indexes():
    return [write_index(group) for group in list(settings.ES_WRITE_INDEXES.keys())]


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


class AnalyzerMixin(object):

    def _with_analyzer(self, key, val, action):
        """Do a normal kind of query, with a analyzer added.

        :arg key: is the field being searched
        :arg val: Is a two-tupe of the text to query for and the name of
            the analyzer to use.
        :arg action: is the type of query being performed, like match or
            match_phrase
        """
        query, analyzer = val
        clause = {
            action: {
                key: {
                    'query': query,
                    'analyzer': analyzer,
                }
            }
        }

        boost = self.field_boosts.get(key)
        if boost is not None:
            clause[action][key]['boost'] = boost

        return clause

    def process_query_match_phrase_analyzer(self, key, val, action):
        """A match phrase query that includes an analyzer."""
        return self._with_analyzer(key, val, 'match_phrase')

    def process_query_match_analyzer(self, key, val, action):
        """A match query that includes an analyzer."""
        return self._with_analyzer(key, val, 'match')

    def process_query_sqs(self, key, val, action):
        """Implements simple_query_string query"""
        return {
            'simple_query_string': {
                'fields': [key],
                'query': val,
                'default_operator': 'or',
            }
        }

    def process_query_sqs_analyzer(self, key, val, action):
        """Implements sqs query that includes an analyzer"""
        query, analyzer = val
        return {
            'simple_query_string': {
                'fields': [key],
                'query': query,
                'analyzer': analyzer,
                'default_operator': 'or',
            }
        }

    def process_query_match_whitespace(self, key, val, action):
        """A match query that uses the whitespace analyzer."""
        return {
            'match': {
                key: {
                    'query': val,
                    'analyzer': 'whitespace',
                }
            }
        }


class Sphilastic(S, AnalyzerMixin):
    """Shim around elasticutils.contrib.django.S.

    Implements some Kitsune-specific behavior to make our lives
    easier.

    .. Note::

       This looks at the read index. If you need to look at something
       different, build your own S.

    """
    def print_query(self):
        pprint.pprint(self._build_query())

    def get_indexes(self):
        # SphilasticUnified is a searcher and so it's _always_ used in
        # a read context. Therefore, we always return the read index.
        return [read_index(self.type.get_index_group())]

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


class AnalyzerS(UntypedS, AnalyzerMixin):
    """This is to give the search view support for setting the analyzer.

    This differs from Sphilastic in that this is a plain ES S object,
    not based on Django.

    This just exists as a way to mix together UntypedS and AnalyzerMixin.
    """
    pass


def get_mappings(index):
    mappings = {}

    from kitsune.search.models import get_mapping_types
    for cls in get_mapping_types():
        group = cls.get_index_group()
        if index == write_index(group) or index == read_index(group):
            mappings[cls.get_mapping_type_name()] = cls.get_mapping()

    return mappings


def get_all_mappings():
    mappings = {}

    from kitsune.search.models import get_mapping_types
    for cls in get_mapping_types():
        mappings[cls.get_mapping_type_name()] = cls.get_mapping()

    return mappings


def get_indexes(all_indexes=False):
    """Query ES to get a list of indexes that actually exist.

    :returns: A dict like {index_name: document_count}.
    """
    es = get_es()
    status = es.indices.status()
    indexes = status['indices']

    if not all_indexes:
        indexes = dict((k, v) for k, v in list(indexes.items())
                       if k.startswith(settings.ES_INDEX_PREFIX))

    return [(name, value['docs']['num_docs'])
            for name, value in list(indexes.items())]


def get_doctype_stats(index):
    """Returns a dict of name -> count for documents indexed.

    For example:

    >>> get_doctype_stats()
    {'questions_question': 14216, 'forums_thread': 419, 'wiki_document': 759}

    :throws elasticsearch.exceptions.ConnectionError: if there is a
        connection error, including a timeout.
    :throws elasticsearch.exceptions.NotFound: if the index doesn't exist

    """
    stats = {}

    from kitsune.search.models import get_mapping_types
    for cls in get_mapping_types():
        if cls.get_index() == index:
            # Note: Can't use cls.search() here since that returns a
            # Sphilastic which is hard-coded to look only at the
            # read index..
            s = S(cls).indexes(index)
            stats[cls.get_mapping_type_name()] = s.count()

    return stats


def delete_index(index):
    get_es().indices.delete(index=index, ignore=[404])


def format_time(time_to_go):
    """Returns minutes and seconds string for given time in seconds"""
    if time_to_go < 60:
        return "%ds" % time_to_go
    return "%dm %ds" % (time_to_go / 60, time_to_go % 60)


def get_documents(cls, ids):
    """Returns a list of ES documents with specified ids and doctype

    :arg cls: the mapping type class with a ``.search()`` to use
    :arg ids: the list of ids to retrieve documents for

    :returns: list of documents as dicts
    """
    # FIXME: We pull the field names from the mapping, but I'm not
    # sure if this works in all cases or not and it's kind of hacky.
    fields = list(cls.get_mapping()['properties'].keys())
    ret = cls.search().filter(id__in=ids).values_dict(*fields)[:len(ids)]
    return cls.reshape(ret)


def get_analysis():
    """Generate all our custom analyzers, tokenizers, and filters

    These are variants of the Snowball analyzer for various languages,
    but could also include custom analyzers if the need arises.
    """
    analyzers = {}
    filters = {}

    # The keys are locales to look up to decide the analyzer's name.
    # The values are the language name to set for Snowball.
    snowball_langs = {
        'eu': 'Basque',
        'ca': 'Catalan',
        'da': 'Danish',
        'nl': 'Dutch',
        'en-US': 'English',
        'fi': 'Finnish',
        'fr': 'French',
        'de': 'German',
        'hu': 'Hungarian',
        'it': 'Italian',
        'no': 'Norwegian',
        'pt-BR': 'Portuguese',
        'ro': 'Romanian',
        'ru': 'Russian',
        'es': 'Spanish',
        'sv': 'Swedish',
        'tr': 'Turkish',
    }

    for locale, language in list(snowball_langs.items()):
        analyzer_name = es_analyzer_for_locale(locale, synonyms=False)
        analyzers[analyzer_name] = {
            'type': 'snowball',
            'language': language,
        }

        # The snowball analyzer is actually just a shortcut that does
        # a particular set of tokenizers and analyzers. According to
        # the docs, the below is the same as that, plus synonym handling.

        if locale in config.ES_SYNONYM_LOCALES:
            analyzer_name = es_analyzer_for_locale(locale, synonyms=True)
            analyzers[analyzer_name] = {
                'type': 'custom',
                'tokenizer': 'standard',
                'filter': [
                    'standard',
                    'lowercase',
                    'synonyms-' + locale,
                    'stop',
                    'snowball-' + locale,
                ],
            }

    for locale in config.ES_SYNONYM_LOCALES:
        filter_name, filter_body = es_get_synonym_filter(locale)
        filters[filter_name] = filter_body
        filters['snowball-' + locale] = {
            'type': 'snowball',
            'language': snowball_langs[locale],
        }

    # Done!
    return {
        'analyzer': analyzers,
        'filter': filters,
    }


def es_get_synonym_filter(locale):
    # Avoid circular import
    from kitsune.search.models import Synonym

    # The synonym filter doesn't like it if the synonyms list is empty.
    # If there are no synyonms, just make a no-op filter by making a
    # synonym from one word to itself.

    # TODO: Someday this should be something like .filter(locale=locale)
    synonyms = list(Synonym.objects.all()) or ['firefox => firefox']
    name = 'synonyms-' + locale
    body = {
        'type': 'synonym',
        'synonyms': [str(s) for s in synonyms],
    }

    return name, body


def recreate_indexes(es=None, indexes=None):
    """Deletes indexes and recreates them.

    :arg es: An ES object to use. Defaults to calling `get_es()`.
    :arg indexes: A list of indexes to recreate. Defaults to all write
        indexes.
    """
    if es is None:
        es = get_es()
    if indexes is None:
        indexes = all_write_indexes()

    for index in indexes:
        delete_index(index)

        # There should be no mapping-conflict race here since the index doesn't
        # exist. Live indexing should just fail.

        # Simultaneously create the index, the mappings, the analyzers, and
        # the tokenizers, so live indexing doesn't get a chance to index
        # anything between and infer a bogus mapping (which ES then freaks
        # out over when we try to lay in an incompatible explicit mapping).
        es.indices.create(index=index, body={
            'mappings': get_mappings(index),
            'settings': {
                'analysis': get_analysis(),
            }
        })

    # Wait until the index is there.
    es.cluster.health(wait_for_status='yellow')


def get_index_settings(index):
    """Returns ES settings for this index"""
    return (get_es().indices.get_settings(index=index)
            .get(index, {}).get('settings', {}))


def get_indexable(percent=100, seconds_ago=0, mapping_types=None):
    """Returns a list of (class, iterable) for all the things to index

    :arg percent: Defaults to 100.  Allows you to specify how much of
        each doctype you want to index.  This is useful for
        development where doing a full reindex takes an hour.
    :arg mapping_types: The list of mapping types to index.

    """
    from kitsune.search.models import get_mapping_types

    # Note: Passing in None will get all the mapping types
    mapping_types = get_mapping_types(mapping_types)

    to_index = []
    percent = float(percent) / 100
    for cls in mapping_types:
        indexable = cls.get_indexable(seconds_ago=seconds_ago)
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
                   criticalmass=False, seconds_ago=0, log=log):
    """Rebuild ElasticSearch indexes

    :arg percent: 1 to 100--the percentage of the db to index
    :arg delete: whether or not to wipe the index before reindexing
    :arg mapping_types: list of mapping types to index
    :arg criticalmass: whether or not to index just a critical mass of
        things
    :arg seconds_ago: things updated less than this number of seconds
        ago should be reindexed
    :arg log: the logger to use

    """
    es = get_es()

    if mapping_types is None:
        indexes = all_write_indexes()
    else:
        indexes = indexes_for_doctypes(mapping_types)

    need_delete = False
    for index in indexes:
        try:
            # This is used to see if the index exists.
            get_doctype_stats(index)
        except ES_EXCEPTIONS:
            if not delete:
                log.error('The index "%s" does not exist. '
                          'You must specify --delete.' % index)
                need_delete = True
    if need_delete:
        return

    if delete:
        log.info('wiping and recreating %s...', ', '.join(indexes))
        recreate_indexes(es, indexes)

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
        all_indexable = get_indexable(percent, seconds_ago, mapping_types)

    else:
        all_indexable = get_indexable(percent, seconds_ago)

    try:
        old_refreshes = {}
        # We're doing a lot of indexing, so we get the refresh_interval of
        # the index currently, then nix refreshing. Later we'll restore it.
        for index in indexes:
            old_refreshes[index] = (get_index_settings(index)
                                    .get('index.refresh_interval', '1s'))
            # Disable automatic refreshing
            es.indices.put_settings(index=index,
                                    body={'index': {'refresh_interval': '-1'}})

        start_time = time.time()
        for cls, indexable in all_indexable:
            cls_start_time = time.time()
            total = len(indexable)

            if total == 0:
                continue

            chunk_start_time = time.time()
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
                         format_time(time_to_go))

            delta_time = time.time() - cls_start_time
            log.info('   done! (%s total, %s/1000 avg)',
                     format_time(delta_time),
                     format_time(delta_time / (total / 1000.0)))

        delta_time = time.time() - start_time
        log.info('done! (%s total)', format_time(delta_time))

    finally:
        # Re-enable automatic refreshing
        for index, old_refresh in list(old_refreshes.items()):
            es.indices.put_settings(
                index=index,
                body={'index': {'refresh_interval': old_refresh}})


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

    if index in all_read_indexes() and not noinput:
        ret = input('"%s" is a read index. Are you sure you want '
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
        # TODO: SUMO has a single ES_URL and that's the ZLB and does
        # the balancing. If that ever changes and we have multiple
        # ES_URLs, then this should get fixed.
        es_deets = requests.get(settings.ES_URLS[0]).json()
    except requests.exceptions.RequestException:
        pass

    read_doctype_stats = {}
    for index in all_read_indexes():
        try:
            read_doctype_stats[index] = get_doctype_stats(index)
        except ES_EXCEPTIONS:
            read_doctype_stats[index] = None

    if set(all_read_indexes()) == set(all_write_indexes()):
        write_doctype_stats = read_doctype_stats
    else:
        write_doctype_stats = {}
        for index in all_write_indexes():
            try:
                write_doctype_stats[index] = get_doctype_stats(index)
            except ES_EXCEPTIONS:
                write_doctype_stats[index] = None

    try:
        indexes = get_indexes(all_indexes=True)
    except ES_EXCEPTIONS:
        log.error('Your elasticsearch process is not running or ES_URLS '
                  'is set wrong in your settings_local.py file.')
        return

    log.info('Elasticsearch:')
    log.info('  Version                 : %s', es_deets['version']['number'])

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
            if name in all_read_indexes():
                read_write.append('READ')
            if name in all_write_indexes():
                read_write.append('WRITE')
            log.info('    %-22s: %s %s', name, count,
                     '/'.join(read_write))
    else:
        log.info('  There are no %s indexes.', settings.ES_INDEX_PREFIX)

    if not read_doctype_stats:
        read_index_names = ', '.join(all_read_indexes())
        log.info('  No read indexes exist. (%s)', read_index_names)
    else:
        log.info('  Read indexes:')
        for index, stats in list(read_doctype_stats.items()):
            if stats is None:
                log.info('    %s does not exist', index)
            else:
                log.info('    %s:', index)
                for name, count in sorted(stats.items()):
                    log.info('      %-22s: %d', name, count)

    if set(all_read_indexes()) == set(all_write_indexes()):
        log.info('  Write indexes are the same as the read indexes.')
    else:
        if not write_doctype_stats:
            write_index_names = ', '.join(all_write_indexes())
            log.info('  No write indexes exist. (%s)', write_index_names)
        else:
            log.info('  Write indexes:')
            for index, stats in list(write_doctype_stats.items()):
                if stats is None:
                    log.info('    %s does not exist', index)
                else:
                    log.info('    %s:', index)
                    for name, count in sorted(stats.items()):
                        log.info('      %-22s: %d', name, count)

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
            print('There were %d missing_docs' % missing_docs)


def es_search_cmd(query, pages=1, log=log):
    """Simulates a front page search

    .. Note::

       This **doesn't** simulate an advanced search---just a front
       page search.

    """
    from kitsune.sumo.tests import LocalizingClient
    from kitsune.sumo.urlresolvers import reverse

    client = LocalizingClient()

    output = []
    output.append('Search for: %s' % query)
    output.append('')

    data = {'q': query, 'format': 'json'}
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
            results = content['results']

            for mem in results:
                output.append('%4d  %5.2f  %-10s  %-20s' % (
                              mem['rank'], mem['score'], mem['type'],
                              mem['title']))

            output.append('')

    for line in output:
        log.info(line.encode('ascii', 'ignore'))


def es_verify_cmd(log=log):
    log.info('Behold! I am the magificent esverify command and I shall verify')
    log.info('all things verifyable so that you can rest assured that your')
    log.info('changes are bereft of the tawdry clutches of whimsy and')
    log.info('misfortune.')
    log.info('')

    log.info('Verifying mappings do not conflict.')

    # Verify mappings that share the same index don't conflict
    for index in all_write_indexes():
        merged_mapping = {}

        log.info('Verifying mappings for index: {index}'.format(index=index))

        start_time = time.time()
        for cls_name, mapping in list(get_mappings(index).items()):
            mapping = mapping['properties']
            for key, val in list(mapping.items()):
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


def es_analyzer_for_locale(locale, synonyms=False, fallback='standard'):
    """Pick an appropriate analyzer for a given locale.

    If no analyzer is defined for `locale`, return fallback instead,
    which defaults to ES analyzer named "standard".

    If `synonyms` is True, this will return a synonym-using analyzer,
    if that makes sense. In particular, it doesn't make sense to use
    synonyms with the fallback analyzer.
    """

    if locale in settings.ES_LOCALE_ANALYZERS:
        analyzer = settings.ES_LOCALE_ANALYZERS[locale]
        if synonyms and locale in config.ES_SYNONYM_LOCALES:
            analyzer += '-synonyms'
    else:
        analyzer = fallback

    if (not settings.ES_USE_PLUGINS and
            analyzer in settings.ES_PLUGIN_ANALYZERS):
        analyzer = fallback

    return analyzer


def es_query_with_analyzer(query, locale):
    """Transform a query dict to use _analyzer actions for the right fields."""
    analyzer = es_analyzer_for_locale(locale, synonyms=True)
    new_query = {}

    # Import locally to avoid circular import
    from kitsune.search.models import get_mapping_types
    localized_fields = []
    for mt in get_mapping_types():
        localized_fields.extend(mt.get_localized_fields())

    for k, v in list(query.items()):
        field, action = k.split('__')
        if field in localized_fields:
            new_query[k + '_analyzer'] = (v, analyzer)
        else:
            new_query[k] = v

    return new_query


def indexes_for_doctypes(doctype):
    # Import locally to avoid circular import.
    from kitsune.search.models import get_mapping_types
    return set(d.get_index() for d in get_mapping_types(doctype))


def handle_es_errors(template, status_code=503):
    """Handles Elasticsearch exceptions for views

    Wrap the entire view in this and don't worry about Elasticsearch exceptions
    again!

    :arg template: template path string or function to generate the template
        path string for HTML requests
    :arg status_code: status code to return

    :returns: content-type-appropriate HttpResponse

    """
    def handler(fun):
        @wraps(fun)
        def _handler(request, *args, **kwargs):
            try:
                return fun(request, *args, **kwargs)

            except ES_EXCEPTIONS as exc:
                is_json = (request.GET.get('format') == 'json')
                callback = request.GET.get('callback', '').strip()
                content_type = 'application/x-javascript' if callback else 'application/json'
                if is_json:
                    return HttpResponse(
                        json.dumps({'error': _('Search Unavailable')}),
                        content_type=content_type,
                        status=status_code)

                # If template is a function, call it with the request, args
                # and kwargs to get the template.
                if callable(template):
                    actual_template = template(request, *args, **kwargs)
                else:
                    actual_template = template

                # Log exceptions so this isn't failing silently
                log.exception(exc)

                return render(request, actual_template, status=503)

        return _handler
    return handler
