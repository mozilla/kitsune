import logging
from datetime import datetime
from pprint import pformat

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

from search import es_utils
from search.es_utils import (get_doctype_stats, get_indexes, delete_index,
                             ESTimeoutError, ESMaxRetryError,
                             ESIndexMissingException, get_indexable,
                             SUMO_DOCTYPE, merge_mappings, CHUNK_SIZE,
                             recreate_index)
from search.models import Record, get_search_models
from search.tasks import OUTSTANDING_INDEX_CHUNKS, index_chunk_task
from search.utils import chunked, create_batch_id
from sumo.redis_utils import redis_client, RedisError
from wiki.models import Document


log = logging.getLogger('k.es')


def handle_reset(request):
    """Resets the redis scoreboard we use

    Why? The reason you'd want to reset it is if the system gets
    itself into a hosed state where the redis scoreboard says there
    are outstanding tasks, but there aren't. If you enter that state,
    this lets you reset the scoreboard.
    """
    try:
        client = redis_client('default')
        client.set(OUTSTANDING_INDEX_CHUNKS, 0)
    except RedisError:
        log.warning('Redis not running. Can not check if there are '
                    'outstanding tasks.')
    return HttpResponseRedirect(request.path)


class DeleteError(Exception):
    pass


def handle_delete(request):
    """Deletes an index"""
    index_to_delete = request.POST['delete_index']

    # Rule 1: Has to start with the ES_INDEX_PREFIX.
    if not index_to_delete.startswith(settings.ES_INDEX_PREFIX):
        raise DeleteError('"%s" is not a valid index name.' % index_to_delete)

    # Rule 2: Must be an existing index.
    indexes = [name for name, count in get_indexes()]
    if index_to_delete not in indexes:
        raise DeleteError('"%s" does not exist.' % index_to_delete)

    # Rule 3: Don't delete the READ index.
    if index_to_delete == es_utils.READ_INDEX:
        raise DeleteError('"%s" is the read index.' % index_to_delete)

    delete_index(index_to_delete)

    return HttpResponseRedirect(request.path)


class ReindexError(Exception):
    pass


def handle_reindex(request):
    """Caculates and kicks off indexing tasks"""
    write_index = es_utils.WRITE_INDEX

    # This is truthy if the user wants us to delete and recreate
    # the index first.
    delete_index_first = bool(request.POST.get('delete_index'))

    # Get the list of models to reindex.
    models_to_index = [name.replace('check_', '')
                       for name in request.POST.keys()
                       if name.startswith('check_')]

    # TODO: If this gets fux0rd, then it's possible this could be
    # non-zero and we really want to just ignore it. Need the ability
    # to ignore it.
    try:
        client = redis_client('default')
        val = client.get(OUTSTANDING_INDEX_CHUNKS)
        if val is not None and int(val) > 0:
            raise ReindexError('There are %s outstanding chunks.' % val)

        # We don't know how many chunks we're building, but we do want
        # to make sure another reindex request doesn't slide in here
        # and kick off a bunch of chunks.
        #
        # There is a race condition here.
        client.set(OUTSTANDING_INDEX_CHUNKS, 1)
    except RedisError:
        log.warning('Redis not running. Can not check if there are '
                    'outstanding tasks.')

    batch_id = create_batch_id()

    # Break up all the things we want to index into chunks. This
    # chunkifies by class then by chunk size.
    chunks = []
    for cls, indexable in get_indexable(search_models=models_to_index):
        chunks.extend(
            (cls, chunk) for chunk in chunked(indexable, CHUNK_SIZE))

    if delete_index_first:
        # The previous lines do a lot of work and take some time to
        # execute.  So we wait until here to wipe and rebuild the
        # index. That reduces the time that there is no index by a little.
        recreate_index()

    chunks_count = len(chunks)

    try:
        client = redis_client('default')
        client.set(OUTSTANDING_INDEX_CHUNKS, chunks_count)
    except RedisError:
        log.warning('Redis not running. Can\'t denote outstanding tasks.')

    for chunk in chunks:
        index_chunk_task.delay(write_index, batch_id, chunk)

    return HttpResponseRedirect(request.path)


def search(request):
    """Render the admin view containing search tools"""
    if not request.user.has_perm('search.reindex'):
        raise PermissionDenied

    error_messages = []
    stats = {}

    reset_requested = 'reset' in request.POST
    if reset_requested:
        try:
            return handle_reset(request)
        except ReindexError, e:
            error_messages.append(u'Error: %s' % e.message)

    reindex_requested = 'reindex' in request.POST
    if reindex_requested:
        try:
            return handle_reindex(request)
        except ReindexError, e:
            error_messages.append(u'Error: %s' % e.message)

    delete_requested = 'delete_index' in request.POST
    if delete_requested:
        try:
            return handle_delete(request)
        except DeleteError, e:
            error_messages.append(u'Error: %s' % e.message)
        except ESMaxRetryError:
            error_messages.append('Error: Elastic Search is not set up on '
                                  'this machine or is not responding. '
                                  '(MaxRetryError)')
        except ESIndexMissingException:
            error_messages.append('Error: Index is missing. Press the reindex '
                                  'button below. (IndexMissingException)')
        except ESTimeoutError:
            error_messages.append('Error: Connection to Elastic Search timed '
                                  'out. (TimeoutError)')

    stats = None
    write_stats = None
    indexes = []
    try:
        # This gets index stats, but also tells us whether ES is in
        # a bad state.
        try:
            stats = get_doctype_stats(es_utils.READ_INDEX)
        except ESIndexMissingException:
            stats = None
        try:
            write_stats = get_doctype_stats(es_utils.WRITE_INDEX)
        except ESIndexMissingException:
            write_stats = None
        indexes = get_indexes()
        indexes.sort(key=lambda m: m[0])
    except ESMaxRetryError:
        error_messages.append('Error: Elastic Search is not set up on this '
                              'machine or is not responding. (MaxRetryError)')
    except ESIndexMissingException:
        error_messages.append('Error: Index is missing. Press the reindex '
                              'button below. (IndexMissingException)')
    except ESTimeoutError:
        error_messages.append('Error: Connection to Elastic Search timed out. '
                              '(TimeoutError)')

    try:
        client = redis_client('default')
        outstanding_chunks = int(client.get(OUTSTANDING_INDEX_CHUNKS))
    except (RedisError, TypeError):
        outstanding_chunks = None

    recent_records = Record.uncached.order_by('-starttime')[:20]

    return render_to_response(
        'search/admin/search.html',
        {'title': 'Search',
         'doctype_stats': stats,
         'doctype_write_stats': write_stats,
         'indexes': indexes,
         'read_index': es_utils.READ_INDEX,
         'write_index': es_utils.WRITE_INDEX,
         'error_messages': error_messages,
         'recent_records': recent_records,
         'outstanding_chunks': outstanding_chunks,
         'now': datetime.now(),
         },
        RequestContext(request, {}))


admin.site.register_view('search', search, 'Search - Index Maintenance')


def _fix_value_dicts(values_dict_list):
    """Takes a values dict returned from an S and humanizes it"""
    for dict_ in values_dict_list:
        # Convert datestamps (which are in seconds since epoch) to
        # Python datetime objects.
        for key in ('indexed_on', 'created', 'updated'):
            if key in dict_:
                dict_[key] = datetime.fromtimestamp(int(dict_[key]))
    return values_dict_list


def index_view(request):
    requested_bucket = request.GET.get('bucket', '')
    requested_id = request.GET.get('id', '')
    last_20_by_bucket = None
    data = None

    bucket_to_model = dict(
        [(cls._meta.db_table, cls) for cls in get_search_models()])

    if requested_bucket and requested_id:
        # Nix whitespace because I keep accidentally picking up spaces
        # when I copy and paste.
        requested_id = requested_id.strip()

        # The user wants to see a specific item in the index, so we
        # attempt to fetch it from the index and show that
        # specifically.
        if requested_bucket not in bucket_to_model:
            raise Http404

        cls = bucket_to_model[requested_bucket]
        data = list(cls.search().filter(id=requested_id).values_dict())
        if not data:
            raise Http404
        data = _fix_value_dicts(data)[0]

    else:
        # Create a list of (class, list-of-dicts) showing us the most
        # recently indexed items for each bucket. We only display the
        # id, title and indexed_on fields, so only pull those back from
        # ES.
        last_20_by_bucket = [
            (cls_name,
             _fix_value_dicts(cls.search()
                                 .values_dict()
                                 .order_by('-indexed_on')[:20]))
            for cls_name, cls in bucket_to_model.items()]

    return render_to_response(
        'search/admin/index.html',
        {'title': 'Index Browsing',
         'buckets': [cls_name for cls_name, cls in bucket_to_model.items()],
         'last_20_by_bucket': last_20_by_bucket,
         'requested_bucket': requested_bucket,
         'requested_id': requested_id,
         'requested_data': data
         },
        RequestContext(request, {}))


admin.site.register_view('index', index_view, 'Search - Index Browsing')


def mapping_view(request):
    search_models = get_search_models()
    merged_mapping = {
        SUMO_DOCTYPE: {
            'properties': merge_mappings(
                [(cls._meta.db_table, cls.get_mapping())
                 for cls in search_models])
            }
        }

    # TODO: This indents poorly and the results are hard to read.  I
    # think to do it better, we'd need to write our own pretty-printer
    # which isn't hard, but I'm pushing it off until we decide it's
    # necessary.
    merged_mapping = pformat(merged_mapping, indent=4)

    return render_to_response(
        'search/admin/mapping.html',
        {'title': 'Mapping Browsing',
         'mapping': merged_mapping
         },
        RequestContext(request, {}))


admin.site.register_view('mapping', mapping_view, 'Search - Mapping Browsing')


def troubleshooting_view(request):
    # Build a list of the most recently indexed 50 wiki documents.
    last_50_indexed = _fix_value_dicts(Document.search()
                                               .values_dict()
                                               .order_by('-indexed_on')[:50])

    last_50_reviewed = (Document.uncached
                                .filter(current_revision__is_approved=True)
                                .order_by('-current_revision__reviewed')[:50])

    return render_to_response(
        'search/admin/troubleshooting.html',
        {'title': 'Index Troubleshooting',
         'last_50_indexed': last_50_indexed,
         'last_50_reviewed': last_50_reviewed
         },
        RequestContext(request, {}))


admin.site.register_view('troubleshooting', troubleshooting_view,
                         'Search - Index Troubleshooting')
