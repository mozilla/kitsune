import logging

from django.shortcuts import render

from statsd import statsd

from kitsune.search.es_utils import ES_EXCEPTIONS, F
from kitsune.users.models import UserMappingType


log = logging.getLogger('k.community')


def home(request):
    """Community hub landing page."""

    data = {}

    return render(request, 'community/index.html', data)


def search(request):
    """Find users by username and displayname.

    Uses the ES user's index.
    """
    results = []
    search_errored = False
    q = request.GET.get('q')

    if q:
        lowerq = q.lower()
        try:
            results = (UserMappingType
                .search()
                .query(
                    iusername__match=lowerq,
                    idisplay_name__match_whitespace=lowerq,
                    should=True)
                .values_dict('id', 'username', 'display_name', 'avatar'))

            statsd.incr('community.usersearch.success')
        except ES_EXCEPTIONS as exc:
            search_errored = True
            statsd.incr('community.usersearch.error')
            log.exception('User search failed.')

    # For now, we're just truncating results at 30 and not doing any
    # pagination. If somebody complains, we can add pagination or something.
    results = list(results[:30])

    data = {
        'q': q,
        'results': results,
        'search_errored': search_errored,
    }

    return render(request, 'community/search.html', data)


def view_all(request):

    data = {}

    return render(request, 'community/view_all.html', data)
