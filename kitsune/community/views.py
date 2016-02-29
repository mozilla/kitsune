import logging
from datetime import datetime

from django.conf import settings
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from statsd import statsd

from kitsune.community import api
from kitsune.community.utils import (
    top_contributors_aoa, top_contributors_questions,
    top_contributors_kb, top_contributors_l10n)
from kitsune.forums.models import Thread
from kitsune.products.models import Product
from kitsune.products.api import ProductSerializer
from kitsune.questions.models import QuestionLocale
from kitsune.search.es_utils import ES_EXCEPTIONS
from kitsune.sumo.api_utils import JSONRenderer
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
        data['top_contributors_aoa'], _ = top_contributors_aoa(locale=locale)

        # If the locale is en-US we should top KB contributors, else we show
        # top l10n contributors for that locale
        if locale == settings.WIKI_DEFAULT_LANGUAGE:
            data['top_contributors_kb'], _ = top_contributors_kb(
                product=product)
        else:
            data['top_contributors_l10n'], _ = top_contributors_l10n(
                locale=locale, product=product)

        # If the locale is enabled for the Support Forum, show the top
        # contributors for that locale
        if locale in QuestionLocale.objects.locales_list():
            data['top_contributors_questions'], _ = top_contributors_questions(
                locale=locale, product=product)
    else:
        # If no locale is specified, we show overall top contributors
        # across locales.
        data['top_contributors_aoa'], _ = top_contributors_aoa()
        data['top_contributors_kb'], _ = top_contributors_kb(product=product)
        data['top_contributors_l10n'], _ = top_contributors_l10n(
            product=product)
        data['top_contributors_questions'], _ = top_contributors_questions(
            product=product)

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
            results = (
                UserMappingType
                .search()
                .query(
                    iusername__match=lowerq,
                    idisplay_name__match_whitespace=lowerq,
                    itwitter_usernames__match=lowerq,
                    should=True)
                .values_dict('id', 'username', 'display_name', 'avatar',
                             'twitter_usernames', 'last_contribution_date'))
            results = UserMappingType.reshape(results)

            statsd.incr('community.usersearch.success')
        except ES_EXCEPTIONS:
            search_errored = True
            statsd.incr('community.usersearch.error')
            log.exception('User search failed.')

    # For now, we're just truncating results at 30 and not doing any
    # pagination. If somebody complains, we can add pagination or something.
    results = list(results[:30])

    # Calculate days since last activity.
    for r in results:
        lcd = r.get('last_contribution_date', None)
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


def metrics(request):
    return render(request, 'community/metrics.html')


def top_contributors(request, area):
    """Top contributors list view."""

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    page_size = 100

    locale = _validate_locale(request.GET.get('locale'))
    product = request.GET.get('product')
    if product:
        product = get_object_or_404(Product, slug=product)

    if area == 'army-of-awesome':
        results, total = top_contributors_aoa(
            locale=locale, count=page_size, page=page)
        locales = settings.SUMO_LANGUAGES
    elif area == 'questions':
        results, total = top_contributors_questions(
            locale=locale, product=product, count=page_size, page=page)
        locales = QuestionLocale.objects.locales_list()
    elif area == 'kb':
        results, total = top_contributors_kb(
            product=product, count=page_size, page=page)
        locales = None
    elif area == 'l10n':
        results, total = top_contributors_l10n(
            locale=locale, product=product, count=page_size, page=page)
        locales = settings.SUMO_LANGUAGES
    else:
        raise Http404

    return render(request, 'community/top_contributors.html', {
        'results': results,
        'total': total,
        'area': area,
        'locale': locale,
        'locales': locales,
        'product': product,
        'products': Product.objects.filter(visible=True),
        'page': page,
        'page_size': page_size,
    })


def top_contributors_new(request, area):
    to_json = JSONRenderer().render

    if area == 'questions':
        api_endpoint = api.TopContributorsQuestions
        locales = sorted((settings.LOCALES[code].english, code)
                         for code in QuestionLocale.objects.locales_list())
    elif area == 'l10n':
        api_endpoint = api.TopContributorsLocalization
        locales = sorted((settings.LOCALES[code].english, code)
                         for code in settings.SUMO_LANGUAGES)
    else:
        raise Http404

    if request.LANGUAGE_CODE != 'en-US' and request.LANGUAGE_CODE in [l[1] for l in locales]:
        new_get = {'locale': request.LANGUAGE_CODE}
        new_get.update(request.GET)
        request.GET = new_get

    contributors = api_endpoint().get_data(request)
    products = ProductSerializer(Product.objects.filter(visible=True), many=True)

    return render(request, 'community/top_contributors_react.html', {
        'area': area,
        'contributors_json': to_json(contributors),
        'locales_json': to_json(locales),
        'products_json': to_json(products.data),
    })


def _validate_locale(locale):
    """Make sure the locale is enabled on SUMO."""
    if locale and locale not in settings.SUMO_LANGUAGES:
        raise Http404

    return locale
