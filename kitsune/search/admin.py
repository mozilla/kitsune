import logging
from datetime import datetime
from difflib import SequenceMatcher

import requests

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

from kitsune.search.es_utils import (
    get_doctype_stats, get_indexes, delete_index, ES_EXCEPTIONS,
    get_indexable, CHUNK_SIZE, recreate_indexes, write_index, read_index,
    all_read_indexes, all_write_indexes, indexes_for_doctypes)
from kitsune.search.models import Record, get_mapping_types
from kitsune.search.tasks import (
    OUTSTANDING_INDEX_CHUNKS, index_chunk_task, reconcile_task)
from kitsune.search.utils import chunked, create_batch_id
from kitsune.sumo.redis_utils import redis_client, RedisError
from kitsune.wiki.models import Document, DocumentMappingType


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
    index_to_delete = request.POST.get('delete_index')
    es_indexes = [name for (name, count) in get_indexes()]

    # Rule 1: Has to start with the ES_INDEX_PREFIX.
    if not index_to_delete.startswith(settings.ES_INDEX_PREFIX):
        raise DeleteError('"%s" is not a valid index name.' % index_to_delete)

    # Rule 2: Must be an existing index.
    if index_to_delete not in es_indexes:
        raise DeleteError('"%s" does not exist.' % index_to_delete)

    # Rule 3: Don't delete the default read index.
    # TODO: When the critical index exists, this should be "Don't
    # delete the critical read index."
    if index_to_delete == read_index('default'):
        raise DeleteError('"%s" is the default read index.' % index_to_delete)

    # The index is ok to delete
    delete_index(index_to_delete)

    return HttpResponseRedirect(request.path)


class ReindexError(Exception):
    pass


def reindex_with_scoreboard(mapping_type_names):
    """Reindex all instances of a given mapping type with celery tasks.

    This will use Redis to keep track of outstanding tasks so nothing
    gets screwed up by two jobs running at once.
    """
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
    # chunkifies by class then by chunk size. Also generate
    # reconcile_tasks.
    chunks = []
    for cls, indexable in get_indexable(mapping_types=mapping_type_names):
        chunks.extend(
            (cls, chunk) for chunk in chunked(indexable, CHUNK_SIZE))

        reconcile_task.delay(cls.get_index(), batch_id, cls.get_mapping_type_name())

    chunks_count = len(chunks)

    try:
        client = redis_client('default')
        client.set(OUTSTANDING_INDEX_CHUNKS, chunks_count)
    except RedisError:
        log.warning('Redis not running. Can\'t denote outstanding tasks.')

    for chunk in chunks:
        index = chunk[0].get_index()
        index_chunk_task.delay(index, batch_id, chunk)


def handle_recreate_index(request):
    """Deletes an index, recreates it, and reindexes it."""
    groups = [name.replace('check_', '')
              for name in request.POST.keys()
              if name.startswith('check_')]

    indexes = [write_index(group) for group in groups]
    recreate_indexes(indexes=indexes)

    mapping_types_names = [mt.get_mapping_type_name()
                           for mt in get_mapping_types()
                           if mt.get_index_group() in groups]
    reindex_with_scoreboard(mapping_types_names)

    return HttpResponseRedirect(request.path)


def handle_reindex(request):
    """Caculates and kicks off indexing tasks"""
    mapping_type_names = [name.replace('check_', '')
                          for name in request.POST.keys()
                          if name.startswith('check_')]

    reindex_with_scoreboard(mapping_type_names)

    return HttpResponseRedirect(request.path)


def search(request):
    """Render the admin view containing search tools"""
    if not request.user.has_perm('search.reindex'):
        raise PermissionDenied

    error_messages = []
    stats = {}

    if 'reset' in request.POST:
        try:
            return handle_reset(request)
        except ReindexError as e:
            error_messages.append(u'Error: %s' % e.message)

    if 'reindex' in request.POST:
        try:
            return handle_reindex(request)
        except ReindexError as e:
            error_messages.append(u'Error: %s' % e.message)

    if 'recreate_index' in request.POST:
        try:
            return handle_recreate_index(request)
        except ReindexError as e:
            error_messages.append(u'Error: %s' % e.message)

    if 'delete_index' in request.POST:
        try:
            return handle_delete(request)
        except DeleteError as e:
            error_messages.append(u'Error: %s' % e.message)
        except ES_EXCEPTIONS as e:
            error_messages.append('Error: {0}'.format(repr(e)))

    stats = None
    write_stats = None
    es_deets = None
    indexes = []
    outstanding_chunks = None

    try:
        # TODO: SUMO has a single ES_URL and that's the ZLB and does
        # the balancing. If that ever changes and we have multiple
        # ES_URLs, then this should get fixed.
        es_deets = requests.get(settings.ES_URLS[0]).json()
    except requests.exceptions.RequestException:
        pass

    stats = {}
    for index in all_read_indexes():
        try:
            stats[index] = get_doctype_stats(index)
        except ES_EXCEPTIONS:
            stats[index] = None

    write_stats = {}
    for index in all_write_indexes():
        try:
            write_stats[index] = get_doctype_stats(index)
        except ES_EXCEPTIONS:
            write_stats[index] = None

    try:
        indexes = get_indexes()
        indexes.sort(key=lambda m: m[0])
    except ES_EXCEPTIONS as e:
        error_messages.append('Error: {0}'.format(repr(e)))

    try:
        client = redis_client('default')
        outstanding_chunks = int(client.get(OUTSTANDING_INDEX_CHUNKS))
    except (RedisError, TypeError):
        pass

    recent_records = Record.uncached.order_by('-starttime')[:100]

    outstanding_records = (Record.uncached.filter(endtime__isnull=True)
                                          .order_by('-starttime'))

    index_groups = set(settings.ES_INDEXES.keys())
    index_groups |= set(settings.ES_WRITE_INDEXES.keys())

    index_group_data = [[group, read_index(group), write_index(group)]
                        for group in index_groups]

    return render(
        request,
        'admin/search_maintenance.html',
        {'title': 'Search',
         'es_deets': es_deets,
         'doctype_stats': stats,
         'doctype_write_stats': write_stats,
         'indexes': indexes,
         'index_groups': index_groups,
         'index_group_data': index_group_data,
         'read_indexes': all_read_indexes,
         'write_indexes': all_write_indexes,
         'error_messages': error_messages,
         'recent_records': recent_records,
         'outstanding_records': outstanding_records,
         'outstanding_chunks': outstanding_chunks,
         'now': datetime.now(),
         'read_index': read_index,
         'write_index': write_index,
         })


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
        [(cls.get_mapping_type_name(), cls) for cls in get_mapping_types()])

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

    return render(
        request,
        'admin/search_index.html',
        {'title': 'Index Browsing',
         'buckets': [cls_name for cls_name, cls in bucket_to_model.items()],
         'last_20_by_bucket': last_20_by_bucket,
         'requested_bucket': requested_bucket,
         'requested_id': requested_id,
         'requested_data': data
         })


admin.site.register_view('index', index_view, 'Search - Index Browsing')


class HashableWrapper(object):
    def __init__(self, hashcode, obj):
        self.hashcode = hashcode
        self.obj = obj

    def __hash__(self):
        return hash(self.hashcode)

    def __eq__(self, obj):
        return self.hashcode == obj.hashcode

    def __unicode__(self):
        return repr(self.hashcode)

    __str__ = __unicode__
    __repr__ = __unicode__


def diff_it_for_realz(seq_a, seq_b):
    # In order to get a nice diff of the two lists that shows us what
    # has been updated in the db and has not been indexed in an easy
    # to parse way, we hash the items in each list on an (id, date)
    # tuple. That's used to produce the diff.
    #
    # This gets us really close to something that looks good, though
    # it'll probably have problems if it's changed in the db just
    # before midnight and gets indexed just after midnight--the hashes
    # won't match. It's close, though.
    seq_a = [
        HashableWrapper(
            (doc['id'], datetime.date(doc['indexed_on'])), doc)
        for doc in seq_a]
    seq_b = [
        HashableWrapper(
            (doc.id, datetime.date(doc.current_revision.reviewed)), doc)
        for doc in seq_b]

    opcodes = SequenceMatcher(None, seq_a, seq_b).get_opcodes()
    results = []

    for tag, i1, i2, j1, j2 in opcodes:
        print tag, i1, i2, j1, j2
        if tag == 'equal':
            for i, j in zip(seq_a[i1:i2], seq_b[j1:j2]):
                results.append((i.obj, j.obj))
        elif tag == 'delete':
            # seq_a is missing things that seq_b has
            for j in seq_b[j1:j2]:
                results.append((None, j.obj))
        elif tag == 'insert':
            # seq_a has things seq_b is missing
            for i in seq_a[i1:i2]:
                results.append((i.obj, None))
        elif tag == 'replace':
            # Sort the items in this section by the datetime stamp.
            section = []
            for i in seq_a[i1:i2]:
                section.append((i.obj['indexed_on'], i.obj, None))
            for j in seq_b[j1:j2]:
                section.append((j.obj.current_revision.reviewed, None, j.obj))

            for ignore, i, j in sorted(section, reverse=1):
                results.append((i, j))

    return results


def troubleshooting_view(request):
    # Build a list of the most recently indexed 50 wiki documents.
    last_50_indexed = list(_fix_value_dicts(DocumentMappingType.search()
                                            .values_dict()
                                            .order_by('-indexed_on')[:50]))

    last_50_reviewed = list(Document.uncached
                            .filter(current_revision__is_approved=True)
                            .order_by('-current_revision__reviewed')[:50])

    diff_list = diff_it_for_realz(last_50_indexed, last_50_reviewed)

    return render(
        request,
        'admin/search_troubleshooting.html',
        {'title': 'Index Troubleshooting',
         'diffs': diff_list,
         })


admin.site.register_view('troubleshooting', troubleshooting_view,
                         'Search - Index Troubleshooting')
