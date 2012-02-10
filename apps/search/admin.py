from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.template import RequestContext

from search.es_utils import get_doctype_stats, get_indexes
from search.tasks import (ES_REINDEX_PROGRESS, ES_WAFFLE_WHEN_DONE,
                          reindex_with_progress)
from sumo.urlresolvers import reverse

from search.es_utils import (ESTimeoutError, ESMaxRetryError,
                             ESIndexMissingException)


def search(request):
    """Render the admin view containing search tools.

    It's a dirty little secret that you can fire off 2 concurrent reindexing
    jobs; the disabling of the buttons while one is running is advisory only.
    This lets us recover if celery crashes and doesn't clear the memcached
    token.

    """
    if not request.user.has_perm('search.reindex'):
        raise PermissionDenied

    reindex_requested = 'reindex' in request.POST
    if reindex_requested:
        reindex_with_progress.delay(
                waffle_when_done='waffle_when_done' in request.POST)

    es_error_message = ''
    stats = {}

    read_index = settings.ES_INDEXES['default']
    write_index = settings.ES_WRITE_INDEXES['default']
    try:
        # This gets index stats, but also tells us whether ES is in
        # a bad state.
        stats = get_doctype_stats(read_index)
        write_stats = get_doctype_stats(write_index)
        indexes = get_indexes()
    except ESMaxRetryError:
        es_error_message = ('Elastic Search is not set up on this machine '
                            'or is not responding. (MaxRetryError)')
    except ESIndexMissingException:
        es_error_message = ('Index is missing. Press the reindex button '
                            'below. (IndexMissingException)')
    except ESTimeoutError:
        es_error_message = ('Connection to Elastic Search timed out. '
                            '(TimeoutError)')

    return render_to_response(
        'search/admin/search.html',
        {'title': 'Search',
         'doctype_stats': stats,
         'doctype_write_stats': write_stats,
         'indexes': indexes,
         'read_index': read_index,
         'write_index': write_index,
         'es_error_message': es_error_message,
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
