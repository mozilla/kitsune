import json

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import pgettext
from django.utils.translation import ugettext as _

from kitsune import search as constants
from kitsune.products.models import Product
from kitsune.search.forms import SimpleSearchForm
from kitsune.search.utils import locale_or_default
from kitsune.search.v2.base import SumoSearchPaginator
from kitsune.search.v2.search import CompoundSearch, QuestionSearch, WikiSearch
from kitsune.search.views import _fallback_results
from kitsune.sumo.api_utils import JSONRenderer
from kitsune.sumo.templatetags.jinja_helpers import Paginator as PaginatorRenderer
from kitsune.sumo.utils import paginate


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
    return HttpResponse(json_data, content_type="application/json")


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
