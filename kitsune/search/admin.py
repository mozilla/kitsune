import logging
import time
from datetime import datetime

import requests

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render

from kitsune.search import synonym_utils
from kitsune.search.es_utils import (
    get_doctype_stats, get_indexes, delete_index, ES_EXCEPTIONS,
    get_indexable, CHUNK_SIZE, recreate_indexes, write_index, read_index,
    all_read_indexes, all_write_indexes)
from kitsune.search.models import Record, get_mapping_types, Synonym
from kitsune.search.tasks import index_chunk_task, update_synonyms_task
from kitsune.search.utils import chunked, to_class_path


log = logging.getLogger('k.es')


def handle_reset(request):
    """Resets records"""
    for rec in Record.objects.outstanding():
        rec.mark_fail('Cancelled.')

    return HttpResponseRedirect(request.path)


class DeleteError(Exception):
    pass


def create_batch_id():
    """Returns a batch_id"""
    # TODO: This is silly, but it's a good enough way to distinguish
    # between batches by looking at a Record. This is just over the
    # number of seconds in a day.
    return str(int(time.time()))[-6:]


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


def reindex(mapping_type_names):
    """Reindex all instances of a given mapping type with celery tasks

    :arg mapping_type_names: list of mapping types to reindex

    """
    outstanding = Record.objects.outstanding().count()
    if outstanding > 0:
        raise ReindexError('There are %s outstanding chunks.' % outstanding)

    batch_id = create_batch_id()

    # Break up all the things we want to index into chunks. This
    # chunkifies by class then by chunk size.
    chunks = []
    for cls, indexable in get_indexable(mapping_types=mapping_type_names):
        chunks.extend(
            (cls, chunk) for chunk in chunked(indexable, CHUNK_SIZE))

    for cls, id_list in chunks:
        index = cls.get_index()
        chunk_name = 'Indexing: %s %d -> %d' % (
            cls.get_mapping_type_name(), id_list[0], id_list[-1])
        rec = Record.objects.create(batch_id=batch_id, name=chunk_name)
        index_chunk_task.delay(index, batch_id, rec.id, (to_class_path(cls), id_list))


def handle_recreate_index(request):
    """Deletes an index, recreates it, and reindexes it."""
    groups = [name.replace('check_', '')
              for name in list(request.POST.keys())
              if name.startswith('check_')]

    indexes = [write_index(group) for group in groups]
    recreate_indexes(indexes=indexes)

    mapping_types_names = [mt.get_mapping_type_name()
                           for mt in get_mapping_types()
                           if mt.get_index_group() in groups]
    reindex(mapping_types_names)

    return HttpResponseRedirect(request.path)


def handle_reindex(request):
    """Caculates and kicks off indexing tasks"""
    mapping_type_names = [name.replace('check_', '')
                          for name in list(request.POST.keys())
                          if name.startswith('check_')]

    reindex(mapping_type_names)

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
            error_messages.append('Error: %s' % e.message)

    if 'reindex' in request.POST:
        try:
            return handle_reindex(request)
        except ReindexError as e:
            error_messages.append('Error: %s' % e.message)

    if 'recreate_index' in request.POST:
        try:
            return handle_recreate_index(request)
        except ReindexError as e:
            error_messages.append('Error: %s' % e.message)

    if 'delete_index' in request.POST:
        try:
            return handle_delete(request)
        except DeleteError as e:
            error_messages.append('Error: %s' % e.message)
        except ES_EXCEPTIONS as e:
            error_messages.append('Error: {0}'.format(repr(e)))

    stats = None
    write_stats = None
    es_deets = None
    indexes = []

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

    recent_records = Record.objects.all()[:100]
    outstanding_records = Record.objects.outstanding()

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
         'now': datetime.now(),
         'read_index': read_index,
         'write_index': write_index,
         })


admin.site.register_view(path='search-maintenance', view=search,
                         name='Search - Index Maintenance')


def _fix_results(results):
    """Fixes up the S results for better templating

    1. extract the results_dict from the DefaultMappingType
       and returns that as a dict
    2. turns datestamps into Python datetime objects

    Note: This abuses ElasticUtils DefaultMappingType by using
    the private _results_dict.

    """
    results = [obj._results_dict for obj in results]
    for obj in results:
        # Convert datestamps (which are in seconds since epoch) to
        # Python datetime objects.
        for key in ('indexed_on', 'created', 'updated'):
            if key in obj and not isinstance(obj[key], datetime):
                obj[key] = datetime.fromtimestamp(int(obj[key]))
    return results


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
        data = list(cls.search().filter(id=requested_id))
        if not data:
            raise Http404
        data = _fix_results(data)[0]

    else:
        # Create a list of (class, list-of-dicts) showing us the most
        # recently indexed items for each bucket. We only display the
        # id, title and indexed_on fields, so only pull those back from
        # ES.
        last_20_by_bucket = [
            (cls_name,
             _fix_results(cls.search().order_by('-indexed_on')[:20]))
            for cls_name, cls in list(bucket_to_model.items())]

    return render(
        request,
        'admin/search_index.html',
        {'title': 'Index Browsing',
         'buckets': [cls_name for cls_name, cls in list(bucket_to_model.items())],
         'last_20_by_bucket': last_20_by_bucket,
         'requested_bucket': requested_bucket,
         'requested_id': requested_id,
         'requested_data': data
         })


admin.site.register_view(path='search-index', view=index_view,
                         name='Search - Index Browsing')


class SynonymAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_words', 'to_words')
    list_display_links = ('id', )
    list_editable = ('from_words', 'to_words')
    ordering = ('from_words', 'id')


admin.site.register(Synonym, SynonymAdmin)


def synonym_editor(request):
    parse_errors = []
    all_synonyms = Synonym.objects.all()

    if 'sync_synonyms' in request.POST:
        # This is a task. Normally we would call tasks asyncronously, right?
        # In this case, since it runs quickly and is in the admin interface,
        # the advantage of it being run in the request/response cycle
        # outweight the delay in responding. If this becomes a problem
        # we should make a better UI and make this .delay() again.
        update_synonyms_task()
        return HttpResponseRedirect(request.path)

    synonyms_text = request.POST.get('synonyms_text')
    if synonyms_text is not None:
        db_syns = set((s.from_words, s.to_words) for s in all_synonyms)

        try:
            post_syns = set(synonym_utils.parse_synonyms(synonyms_text))
        except synonym_utils.SynonymParseError as e:
            parse_errors = e.errors
        else:
            syns_to_add = post_syns - db_syns
            syns_to_remove = db_syns - post_syns

            for (from_words, to_words) in syns_to_remove:
                # This uses .get() because I want it to blow up if
                # there isn't exactly 1 matching synonym.
                (Synonym.objects.get(from_words=from_words, to_words=to_words)
                 .delete())

            for (from_words, to_words) in syns_to_add:
                Synonym(from_words=from_words, to_words=to_words).save()

            return HttpResponseRedirect(request.path)

    # If synonyms_text is not None, it came from POST, and there were
    # errors. It shouldn't be modified, so the error messages make sense.
    if synonyms_text is None:
        synonyms_text = '\n'.join(str(s) for s in all_synonyms)

    synonym_add_count, synonym_remove_count = synonym_utils.count_out_of_date()

    return render(request, 'admin/search_synonyms.html', {
        'synonyms_text': synonyms_text,
        'errors': parse_errors,
        'synonym_add_count': synonym_add_count,
        'synonym_remove_count': synonym_remove_count,
    })


admin.site.register_view(path='synonym_bulk', view=synonym_editor,
                         name='Search - Synonym Editor')
