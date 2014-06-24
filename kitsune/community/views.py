import logging

from django.http import Http404
from django.shortcuts import render

from statsd import statsd

from kitsune.community.utils import (
    top_contributors_aoa, top_contributors_questions,
    top_contributors_kb, top_contributors_l10n)
from kitsune.search.es_utils import ES_EXCEPTIONS, F
from kitsune.users.models import UserMappingType


log = logging.getLogger('k.community')


def home(request):
    """Community hub landing page."""

    return render(request, 'community/index.html', {
        'top_contributors_aoa': top_contributors_aoa(),
        'top_contributors_kb': top_contributors_kb(),
        'top_contributors_l10n': top_contributors_l10n(),
        'top_contributors_questions': top_contributors_questions(),
    })


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


def top_contributors(request, area):
    """Top contributors list view."""

    locale = request.GET.get('locale')

    if area == 'army-of-awesome':
        results = top_contributors_aoa(count=50)
    elif area == 'questions':
        results = top_contributors_questions(locale=locale, count=50)
    elif area == 'kb':
        results = top_contributors_kb(count=50)
    elif area == 'l10n':
        results = top_contributors_l10n(locale=locale, count=50)
    else:
        raise Http404

    return render(request, 'community/top_contributors.html', {
        'results': results,
        'area': area,
    })
