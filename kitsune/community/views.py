import logging

from django.conf import settings
from django.contrib.auth.models import Group
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from kitsune.community.utils import (
    top_contributors_kb,
    top_contributors_l10n,
    top_contributors_questions,
)
from kitsune.forums.models import Thread
from kitsune.products.models import Product
from kitsune.questions.models import QuestionLocale
from kitsune.search.base import SumoSearchPaginator
from kitsune.search.search import ProfileSearch
from kitsune.sumo.parser import get_object_fallback
from kitsune.sumo.utils import paginate
from kitsune.users.models import CONTRIBUTOR_GROUP
from kitsune.wiki.models import Document

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
        data["top_contributors_kb"], _ = top_contributors_kb(product=product)
        data["top_contributors_l10n"], _ = top_contributors_l10n(product=product)
        data["top_contributors_questions"], _ = top_contributors_questions(product=product)

    return render(request, "community/index.html", data)


def search(request):
    """Find users by username and displayname.

    Uses the ES user's index.
    """

    data = {}

    if q := request.GET.get("q"):
        contributor_group_ids = list(
            Group.objects.filter(
                name__in=[
                    "Contributors",
                    CONTRIBUTOR_GROUP,
                ]
            ).values_list("id", flat=True)
        )
        search = ProfileSearch(query=q, group_ids=contributor_group_ids)
        pages = paginate(request, search, paginator_cls=SumoSearchPaginator)
        data = {"q": q, "results": search.results, "pages": pages}

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

    if area == "questions":
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
