import json
import logging
from datetime import timedelta

import waffle
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import pgettext
from django.views.decorators.cache import cache_page

from kitsune import search as constants
from kitsune.products.managers import ProductSupportConfigManager
from kitsune.products.models import Product, ProductSupportConfig
from kitsune.search.base import SumoSearchPaginator
from kitsune.search.forms import SimpleSearchForm
from kitsune.search.hybrid import (
    SEARCH_SESSION_PARAMETER,
    HybridSearchSessionUnavailable,
    run_hybrid_search,
    sources_for_where,
)
from kitsune.search.search import CompoundSearch, QuestionSearch, WikiSearch
from kitsune.search.utils import locale_or_default
from kitsune.sumo.api_utils import JSONRenderer
from kitsune.sumo.templatetags.jinja_helpers import Paginator as PaginatorRenderer
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_aaq_context, get_aaq_url, paginate
from kitsune.wiki.facets import documents_for

log = logging.getLogger("k.search")


def cache_control(resp, cache_period):
    """Inserts cache/expires headers"""
    resp["Cache-Control"] = "max-age=%s" % (cache_period * 60)
    resp["Expires"] = (timezone.now() + timedelta(minutes=cache_period)).strftime(
        "%A, %d %B %Y %H:%M:%S GMT"
    )
    return resp


@cache_page(60 * 60 * 168)  # 1 week.
def opensearch_plugin(request):
    """Render an OpenSearch Plugin."""
    host = "{}://{}".format("https" if request.is_secure() else "http", request.get_host())

    response = render(
        request,
        "search/plugin.html",
        {"host": host, "locale": request.LANGUAGE_CODE},
        content_type="application/opensearchdescription+xml",
    )
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response


def _fallback_results(user, locale, product_slugs):
    """Return the top 20 articles by votes for the given product(s)."""
    products = []
    for slug in product_slugs:
        try:
            p = Product.active.get(slug=slug)
            products.append(p)
        except Product.DoesNotExist:
            pass

    docs, fallback = documents_for(user, locale, products=products)
    docs = docs + (fallback or [])

    return docs[:20]


def _get_product_title(product_title):
    product = Product.active.filter(slug__in=product_title).first()
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

    hybrid = None
    # The form still accepts the legacy discussion value, which retrieval does not index.
    use_hybrid = (
        waffle.switch_is_active("retrieval-hybrid-search")
        and cleaned["w"] != constants.WHERE_DISCUSSION
    )
    if use_hybrid:
        try:
            page_number = int(request.GET.get("page", 1))
        except ValueError:
            page_number = 1
        page_number = max(page_number, 1)
        try:
            hybrid = run_hybrid_search(
                request,
                query=cleaned["q"],
                locale=language,
                sources=sources_for_where(cleaned["w"]),
                product_id=product.id if product else None,
                page=page_number,
                session_token=request.GET.get(SEARCH_SESSION_PARAMETER),
            )
        except HybridSearchSessionUnavailable:
            redirect_params = request.GET.copy()
            redirect_params.pop("page", None)
            redirect_params.pop(SEARCH_SESSION_PARAMETER, None)
            return HttpResponseRedirect(f"{request.path}?{redirect_params.urlencode()}")
        page = None
        results = list(hybrid.results)
        if hybrid.page > 1 and not results and not hybrid.has_next:
            redirect_params = request.GET.copy()
            redirect_params["page"] = 1
            redirect_params.pop(SEARCH_SESSION_PARAMETER, None)
            return HttpResponseRedirect(f"{request.path}?{redirect_params.urlencode()}")
        total = hybrid.approximate_total if results or hybrid.has_next else 0
    else:
        search = CompoundSearch()
        if cleaned["w"] & constants.WHERE_WIKI:
            search.add(WikiSearch(query=cleaned["q"], locale=language, product=product))
        if cleaned["w"] & constants.WHERE_SUPPORT:
            search.add(QuestionSearch(query=cleaned["q"], locale=language, product=product))

        page = paginate(
            request,
            search,
            per_page=settings.SEARCH_RESULTS_PER_PAGE,
            paginator_cls=SumoSearchPaginator,
        )
        total = search.total
        results = search.results

    hybrid_pagination = (
        {
            "number": hybrid.page,
            "has_next": hybrid.has_next,
            "has_previous": hybrid.has_previous,
        }
        if hybrid
        else None
    )

    # generate fallback results if necessary
    fallback_results = None
    if total == 0:
        fallback_results = _fallback_results(request.user, language, cleaned["product"])

    data = {
        "num_results": total,
        "results": results,
        "fallback_results": fallback_results,
        "product_titles": ", ".join(product_titles),
        "q": cleaned["q"],
        "w": cleaned["w"],
        "lang_name": lang_name,
        "products": Product.active.filter(visible=True),
        "total_is_approximate": hybrid is not None,
        "pagination": hybrid_pagination,
        "pagination_url": _hybrid_pagination_url(request, hybrid.session_token) if hybrid else None,
        "search_session": hybrid.session_token if hybrid else None,
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
            "pagination": hybrid_pagination if hybrid else _make_pagination(page),
        }
    )
    if product:
        data["product"] = product.slug
    if not results:
        data["message"] = constants.NO_MATCH

    # Compute the support AAQ URL for the "Still need help?" card.
    # Its presence/absence controls whether the card is shown.
    is_ticketed = False
    support_aaq_url = None
    if not settings.READ_ONLY:
        if product:
            aaq_context = get_aaq_context(request, product)
            support_type = aaq_context.get("current_support_type")
            if support_type and support_type != ProductSupportConfigManager.SUPPORT_TYPE_HIDE:
                support_aaq_url = get_aaq_url(aaq_context)
                is_ticketed = support_type == ProductSupportConfig.SUPPORT_TYPE_ZENDESK
        else:
            support_aaq_url = reverse("questions.aaq_step1")
    data["support_aaq_url"] = support_aaq_url
    data["is_ticketed"] = is_ticketed

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


def _hybrid_pagination_url(request, session_token):
    params = request.GET.copy()
    params.pop("page", None)
    if session_token:
        params[SEARCH_SESSION_PARAMETER] = session_token
    else:
        params.pop(SEARCH_SESSION_PARAMETER, None)
    return f"{request.build_absolute_uri(request.path)}?{params.urlencode()}"
