import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from kitsune.community.utils import (
    top_contributors_aoa,
    top_contributors_questions,
    top_contributors_kb,
    top_contributors_l10n,
)
from kitsune.forums.models import Thread
from kitsune.products.models import Product
from kitsune.questions.models import QuestionLocale
from kitsune.sumo.parser import get_object_fallback
from kitsune.wiki.models import Document

from elasticsearch_dsl import Search
from kitsune.search.v2.es7_utils import es7_client


log = logging.getLogger("k.community")


# Doc for the news section:
COMMUNITY_NEWS_DOC = "Community Hub News"


def home(request):
    """Community hub landing page."""

    community_news = get_object_fallback(Document, COMMUNITY_NEWS_DOC, request.LANGUAGE_CODE)
    locale = _validate_locale(request.GET.get("locale"))
    product = request.GET.get("product")
    if product:
        product = get_object_or_404(Product, slug=product)

    # Get the 5 most recent Community Discussion threads.
    recent_threads = Thread.objects.filter(forum__slug="contributors")[:5]

    data = {
        "community_news": community_news,
        "locale": locale,
        "product": product,
        "products": Product.objects.filter(visible=True),
        "threads": recent_threads,
    }

    if locale:
        data["top_contributors_aoa"], _ = top_contributors_aoa(locale=locale)

        # If the locale is en-US we should top KB contributors, else we show
        # top l10n contributors for that locale
        if locale == settings.WIKI_DEFAULT_LANGUAGE:
            data["top_contributors_kb"], _ = top_contributors_kb(product=product)
        else:
            data["top_contributors_l10n"], _ = top_contributors_l10n(
                locale=locale, product=product
            )

        # If the locale is enabled for the Support Forum, show the top
        # contributors for that locale
        if locale in QuestionLocale.objects.locales_list():
            data["top_contributors_questions"], _ = top_contributors_questions(
                locale=locale, product=product
            )
    else:
        # If no locale is specified, we show overall top contributors
        # across locales.
        data["top_contributors_aoa"], _ = top_contributors_aoa()
        data["top_contributors_kb"], _ = top_contributors_kb(product=product)
        data["top_contributors_l10n"], _ = top_contributors_l10n(product=product)
        data["top_contributors_questions"], _ = top_contributors_questions(product=product)

    return render(request, "community/index.html", data)


def search(request):
    """Find users by username and displayname.

    Uses the ES user's index.
    """
    results = []
    q = request.GET.get("q")

    if q:
        search = Search(using=es7_client(), index="sumo_user").query(
            "simple_query_string", query=q, fields=["username", "name"], default_operator="AND"
        )

        results = search.execute().hits

    # For now, we're just truncating results at 30 and not doing any
    # pagination. If somebody complains, we can add pagination or something.
    results = list(results[:30])

    data = {"q": q, "results": results}

    return render(request, "community/search.html", data)


def metrics(request):
    return render(request, "community/metrics.html")


def top_contributors(request, area):
    """Top contributors list view."""

    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1
    page_size = 100

    locale = _validate_locale(request.GET.get("locale"))
    product = request.GET.get("product")
    if product:
        product = get_object_or_404(Product, slug=product)

    if area == "army-of-awesome":
        results, total = top_contributors_aoa(locale=locale, count=page_size, page=page)
        locales = settings.SUMO_LANGUAGES
    elif area == "questions":
        results, total = top_contributors_questions(
            locale=locale, product=product, count=page_size, page=page
        )
        locales = QuestionLocale.objects.locales_list()
    elif area == "kb":
        results, total = top_contributors_kb(product=product, count=page_size, page=page)
        locales = None
    elif area == "l10n":
        results, total = top_contributors_l10n(
            locale=locale, product=product, count=page_size, page=page
        )
        locales = settings.SUMO_LANGUAGES
    else:
        raise Http404

    return render(
        request,
        "community/top_contributors.html",
        {
            "results": results,
            "total": total,
            "area": area,
            "locale": locale,
            "locales": locales,
            "product": product,
            "products": Product.objects.filter(visible=True),
            "page": page,
            "page_size": page_size,
        },
    )


def _validate_locale(locale):
    """Make sure the locale is enabled on SUMO."""
    if locale and locale not in settings.SUMO_LANGUAGES:
        raise Http404

    return locale
