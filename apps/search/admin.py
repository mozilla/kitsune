from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from search.es_utils import (get_doctype_stats, get_indexes, delete_index,
                             ESTimeoutError, ESMaxRetryError,
                             ESIndexMissingException)
from search.models import Record
from search.tasks import (ES_REINDEX_PROGRESS, ES_WAFFLE_WHEN_DONE,
                          reindex_with_progress)
from sumo.urlresolvers import reverse


class DeleteError(Exception):
    pass


def handle_delete(request):
    index_to_delete = request.POST['delete_index']

    # Rule 1: Has to start with the ES_INDEX_PREFIX.
    if not index_to_delete.startswith(settings.ES_INDEX_PREFIX):
        raise DeleteError('"%s" is not a valid index name.' % index_to_delete)

    # Rule 2: Must be an existing index.
    indexes = [name for name, count in get_indexes()]
    if index_to_delete not in indexes:
        raise DeleteError('"%s" does not exist.' % index_to_delete)

    # Rule 3: Don't delete the READ index.
    if index_to_delete == settings.ES_INDEXES['default']:
        raise DeleteError('"%s" is the read index.' % index_to_delete)

    delete_index(index_to_delete)

    return HttpResponseRedirect(request.path)


def search(request):
    """Render the admin view containing search tools.

    It's a dirty little secret that you can fire off 2 concurrent reindexing
    jobs; the disabling of the buttons while one is running is advisory only.
    This lets us recover if celery crashes and doesn't clear the memcached
    token.

    """
    if not request.user.has_perm('search.reindex'):
        raise PermissionDenied

    delete_error_message = ''
    es_error_message = ''
    stats = {}

    reindex_requested = 'reindex' in request.POST
    if reindex_requested:
        reindex_with_progress.delay(
            waffle_when_done='waffle_when_done' in request.POST)

    delete_requested = 'delete_index' in request.POST
    if delete_requested:
        try:
            return handle_delete(request)
        except DeleteError, e:
            delete_error_message = e.msg
        except ESMaxRetryError:
            delete_error_message = ('Elastic Search is not set up on this '
                                    'machine or is not responding. '
                                    '(MaxRetryError)')
        except ESIndexMissingException:
            delete_error_message = ('Index is missing. Press the reindex '
                                    'button below. (IndexMissingException)')
        except ESTimeoutError:
            delete_error_message = ('Connection to Elastic Search timed out. '
                                    '(TimeoutError)')

    read_index = settings.ES_INDEXES['default']
    write_index = settings.ES_WRITE_INDEXES['default']
    stats = None
    write_stats = None
    indexes = []
    try:
        # This gets index stats, but also tells us whether ES is in
        # a bad state.
        try:
            stats = get_doctype_stats(read_index)
        except ESIndexMissingException:
            stats = None
        try:
            write_stats = get_doctype_stats(write_index)
        except ESIndexMissingException:
            write_stats = None
        indexes = get_indexes()
        indexes.sort(key=lambda m: m[0])
    except ESMaxRetryError:
        es_error_message = ('Elastic Search is not set up on this machine '
                            'or is not responding. (MaxRetryError)')
    except ESIndexMissingException:
        es_error_message = ('Index is missing. Press the reindex button '
                            'below. (IndexMissingException)')
    except ESTimeoutError:
        es_error_message = ('Connection to Elastic Search timed out. '
                            '(TimeoutError)')

    recent_records = reversed(Record.objects.order_by('starttime')[:20])

    return render_to_response(
        'search/admin/search.html',
        {'title': 'Search',
         'doctype_stats': stats,
         'doctype_write_stats': write_stats,
         'indexes': indexes,
         'read_index': read_index,
         'write_index': write_index,
         'delete_error_message': delete_error_message,
         'es_error_message': es_error_message,
         'recent_records': recent_records,
          # Dim the buttons even if the form loads before the task fires:
         'progress': cache.get(ES_REINDEX_PROGRESS,
                               '0.001' if reindex_requested else ''),
         'waffle_when_done':
             request.POST.get('waffle_when_done') if reindex_requested else
             cache.get(ES_WAFFLE_WHEN_DONE),
          'progress_url': reverse('search.reindex_progress'),
          'interval': settings.ES_REINDEX_PROGRESS_BAR_INTERVAL * 1000},
        RequestContext(request, {}))


admin.site.register_view('search', search, 'Search')
