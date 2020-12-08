import json

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext as _, pgettext

from kitsune import search as constants
from kitsune.search.forms import SimpleSearchForm
from kitsune.sumo.api_utils import JSONRenderer
from kitsune.sumo.utils import build_paged_url
from kitsune.products.models import Product
from kitsune.search.views import _fallback_results
from kitsune.search.utils import locale_or_default
from kitsune.search.v2.search import CompoundSearch, QuestionSearch, WikiSearch


def simple_search(request):
    search_form = SimpleSearchForm(request.GET, auto_id=False)

    if not search_form.is_valid():
        return HttpResponse(
            json.dumps({"error": _("Invalid search data.")}),
            content_type="application/json",
            status=400,
        )

    cleaned = search_form.cleaned_data

    # get language
    language = locale_or_default(cleaned["language"] or request.LANGUAGE_CODE)
    lang_name = settings.LANGUAGES_DICT.get(language.lower()) or ""

    # get product
    product = Product.objects.filter(slug__in=cleaned["product"]).first()
    if product:
        product_titles = [pgettext("DB: products.Product.title", product.title)]
    else:
        product_titles = [_("All Products")]

    # get page
    try:
        page = int(request.GET.get("page", 1))
    except ValueError:
        page = 1

    # create search object
    search = CompoundSearch(locale=language, product=product)

    # apply aaq/kb configs
    if cleaned["w"] & constants.WHERE_WIKI:
        search.add(WikiSearch)
    if cleaned["w"] & constants.WHERE_SUPPORT:
        search.add(QuestionSearch)

    # execute search
    search.run(cleaned["q"], page=page)
    total = search.total
    results = search.results

    # generate fallback results if necessary
    fallback_results = None
    if total == 0:
        fallback_results = _fallback_results(language, cleaned["product"])

    # create results dictionary for instant search
    data = {
        "num_results": total,
        "total": total,
        "results": results,
        "fallback_results": fallback_results,
        "product_titles": product_titles,
        "q": cleaned["q"],
        "w": cleaned["w"],
        "lang_name": lang_name,
        "products": [
            {"slug": p.slug, "title": p.title} for p in Product.objects.filter(visible=True)
        ],
        "pagination": _make_pagination(request, page, total),
    }
    if product:
        data["product"] = product.slug
    if not results:
        data["message"] = constants.NO_MATCH

    json_data = JSONRenderer().render(data)
    return HttpResponse(json_data, content_type="application/json")


def _make_pagination(request, page, total):
    num_pages = int(total / 10)

    # logic copied from kitsune.sumo.templatetags.jinja_helper.Paginator
    maximum = 10
    span = (maximum - 1) // 2
    if num_pages < maximum:
        lower, upper = 0, num_pages
    elif page < span + 1:
        lower, upper = 0, span * 2
    elif page > num_pages - span:
        lower, upper = num_pages - span * 2, num_pages
    else:
        lower, upper = page - span, page + span - 1
    page_range = list(range(max(lower + 1, 1), min(total, upper) + 1))

    return {
        "number": page,
        "num_pages": num_pages,
        "has_next": page < num_pages,
        "has_previous": page > num_pages,
        "url": build_paged_url(request),
        "page_range": page_range,
        "dotted_upper": num_pages not in page_range,
        "dotted_lower": 1 not in page_range,
    }
