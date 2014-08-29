import logging
from datetime import datetime

from django.conf import settings
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from statsd import statsd

from kitsune.community.utils import (
    top_contributors_aoa, top_contributors_questions,
    top_contributors_kb, top_contributors_l10n)
from kitsune.forums.models import Thread
from kitsune.products.models import Product
from kitsune.search.es_utils import ES_EXCEPTIONS, F
from kitsune.sumo.parser import get_object_fallback
from kitsune.users.models import UserMappingType
from kitsune.wiki.models import Document


log = logging.getLogger('k.community')


# Doc for the news section:
COMMUNITY_NEWS_DOC = 'Community Hub News'


def home(request):
    """Community hub landing page."""

    community_news = get_object_fallback(
        Document, COMMUNITY_NEWS_DOC, request.LANGUAGE_CODE)
    locale = _validate_locale(request.GET.get('locale'))
    product = request.GET.get('product')
    if product:
        product = get_object_or_404(Product, slug=product)

    # Get the 5 most recent Community Discussion threads.
    recent_threads = Thread.objects.filter(forum__slug='contributors')[:5]

    data = {
        'community_news': community_news,
        'locale': locale,
        'product': product,
        'products': Product.objects.filter(visible=True),
        'threads': recent_threads,
    }

    if locale:
        data['top_contributors_aoa'] = top_contributors_aoa(locale=locale)

        # If the locale is en-US we should top KB contributors, else we show
        # top l10n contributors for that locale
        if locale == settings.WIKI_DEFAULT_LANGUAGE:
            data['top_contributors_kb'] = top_contributors_kb(product=product)
        else:
            data['top_contributors_l10n'] = top_contributors_l10n(
                locale=locale, product=product)

        # If the locale is enabled for the Support Forum, show the top
        # contributors for that locale
        if locale in settings.AAQ_LANGUAGES:
            data['top_contributors_questions'] = top_contributors_questions(
                locale=locale, product=product)
    else:
        # If no locale is specified, we show overall top contributors
        # across locales.
        data['top_contributors_aoa'] = top_contributors_aoa()
        data['top_contributors_kb'] = top_contributors_kb(product=product)
        data['top_contributors_l10n'] = top_contributors_l10n(product=product)
        data['top_contributors_questions'] = top_contributors_questions(product=product)

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
                    itwitter_usernames__match=lowerq,
                    should=True)
                .values_dict('id', 'username', 'display_name', 'avatar',
                             'twitter_usernames', 'last_contribution_date'))

            statsd.incr('community.usersearch.success')
        except ES_EXCEPTIONS as exc:
            search_errored = True
            statsd.incr('community.usersearch.error')
            log.exception('User search failed.')

    # For now, we're just truncating results at 30 and not doing any
    # pagination. If somebody complains, we can add pagination or something.
    results = list(results[:30])

    # Calculate days since last activity.
    for r in results:
        lcd = r['last_contribution_date']
        print lcd
        if lcd:
            delta = datetime.now() - lcd
            r['days_since_last_activity'] = delta.days
        else:
            r['days_since_last_activity'] = None

    data = {
        'q': q,
        'results': results,
        'search_errored': search_errored,
    }

    return render(request, 'community/search.html', data)


def top_contributors(request, area):
    """Top contributors list view."""

    locale = _validate_locale(request.GET.get('locale'))
    product = request.GET.get('product')
    if product:
        product = get_object_or_404(Product, slug=product)

    if area == 'army-of-awesome':
        results = top_contributors_aoa(locale=locale, count=50)
        locales = settings.SUMO_LANGUAGES
    elif area == 'questions':
        results = top_contributors_questions(
            locale=locale, product=product, count=50)
        locales = settings.AAQ_LANGUAGES
    elif area == 'kb':
        results = top_contributors_kb(product=product, count=50)
        locales = None
    elif area == 'l10n':
        results = top_contributors_l10n(
            locale=locale, product=product, count=50)
        locales = settings.SUMO_LANGUAGES
    else:
        raise Http404

    return render(request, 'community/top_contributors.html', {
        'results': results,
        'area': area,
        'locale': locale,
        'locales': locales,
        'product': product,
        'products': Product.objects.filter(visible=True),
    })


def _validate_locale(locale):
    """Make sure the locale is enabled on SUMO."""
    if locale and locale not in settings.SUMO_LANGUAGES:
        raise Http404

    return locale
