import json
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import pgettext
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page

from kitsune import search as constants
from kitsune.products.models import Product
from kitsune.search.base import SumoSearchPaginator
from kitsune.search.forms import SimpleSearchForm
from kitsune.search.search import CompoundSearch, QuestionSearch, WikiSearch
from kitsune.search.utils import locale_or_default
from kitsune.sumo.api_utils import JSONRenderer
from kitsune.sumo.templatetags.jinja_helpers import Paginator as PaginatorRenderer
from kitsune.sumo.utils import paginate
from kitsune.wiki.facets import documents_for

log = logging.getLogger("k.search")


def cache_control(resp, cache_period):
    """Inserts cache/expires headers"""
    resp["Cache-Control"] = "max-age=%s" % (cache_period * 60)
    resp["Expires"] = (datetime.utcnow() + timedelta(minutes=cache_period)).strftime(
        "%A, %d %B %Y %H:%M:%S GMT"
    )
    return resp


@cache_page(60 * 60 * 168)  # 1 week.
def opensearch_plugin(request):
    """Render an OpenSearch Plugin."""
    host = "%s://%s" % ("https" if request.is_secure() else "http", request.get_host())

    response = render(
        request,
        "search/plugin.html",
        {"host": host, "locale": request.LANGUAGE_CODE},
        content_type="application/opensearchdescription+xml",
    )
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def _fallback_results(locale, product_slugs):
    """Return the top 20 articles by votes for the given product(s)."""
    products = []
    for slug in product_slugs:
        try:
            p = Product.objects.get(slug=slug)
            products.append(p)
        except Product.DoesNotExist:
            pass

    docs, fallback = documents_for(locale, products=products)
    docs = docs + (fallback or [])

    return docs[:20]


def _get_product_title(product_title):
    product = Product.objects.filter(slug__in=product_title).first()
    if product:
        product_titles = [pgettext("DB: products.Product.title", product.title)]
    else:
        product_titles = [_("All Products")]
    return product, product_titles


def simple_search(request):
    is_json = request.GET.get("format") == "json"
    search_form = SimpleSearchForm(request.GET, auto_id=False)

    if not search_form.is_valid():
        if not is_json:
            return render(request, "search/form.html", {"search_form": search_form})
        return HttpResponse(
            json.dumps({"error": _("Invalid search data.")}),
            content_type="application/json",
            status=400,
            headers={"X-Robots-Tag": "noindex"},
        )

    cleaned = search_form.cleaned_data

    # get language
    language = locale_or_default(cleaned["language"] or request.LANGUAGE_CODE)
    lang_name = settings.LANGUAGES_DICT.get(language.lower()) or ""

    # get product and product titles
    product, product_titles = _get_product_title(cleaned["product"])

    # create search object
    search = CompoundSearch()

    # apply aaq/kb configs
    if cleaned["w"] & constants.WHERE_WIKI:
        search.add(WikiSearch(query=cleaned["q"], locale=language, product=product))
    if cleaned["w"] & constants.WHERE_SUPPORT:
        search.add(QuestionSearch(query=cleaned["q"], locale=language, product=product))

    # execute search
    page = paginate(
        request,
        search,
        per_page=settings.SEARCH_RESULTS_PER_PAGE,
        paginator_cls=SumoSearchPaginator,
    )
    total = search.total
    results = search.results

    # generate fallback results if necessary
    fallback_results = None
    if total == 0:
        fallback_results = _fallback_results(language, cleaned["product"])

    data = {
        "num_results": total,
        "results": results,
        "fallback_results": fallback_results,
        "product_titles": ", ".join(product_titles),
        "q": cleaned["q"],
        "w": cleaned["w"],
        "lang_name": lang_name,
        "products": Product.objects.filter(visible=True),
    }

    if not is_json:
        data.update(
            {
                "product": product,
                "pages": page,
                "search_form": search_form,
            }
        )
        return render(request, "search/results.html", data)

    # create results dictionary for instant search
    data.update(
        {
            "total": total,
            "products": [
                {"slug": p.slug, "title": pgettext("DB: products.Product.title", p.title)}
                for p in data["products"]
            ],
            "pagination": _make_pagination(page),
        }
    )
    if product:
        data["product"] = product.slug
    if not results:
        data["message"] = constants.NO_MATCH

    json_data = JSONRenderer().render(data)
    return HttpResponse(
        json_data, content_type="application/json", headers={"X-Robots-Tag": "noindex, nofollow"}
    )


def _make_pagination(page):
    jinja_paginator = PaginatorRenderer(page)
    return {
        "number": page.number,
        "num_pages": page.paginator.num_pages,
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "page_range": jinja_paginator.pager.page_range,
        "dotted_upper": jinja_paginator.pager.dotted_upper,
        "dotted_lower": jinja_paginator.pager.dotted_lower,
    }
