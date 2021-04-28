import json
import logging
from datetime import datetime, timedelta
from itertools import chain

import bleach
import jinja2
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, render_to_response
from django.utils.html import escape
from django.utils.http import urlquote
from django.utils.translation import pgettext, pgettext_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page
from elasticutils.contrib.django import ES_EXCEPTIONS
from elasticutils.utils import format_explanation

from kitsune import search as constants
from kitsune.products.models import Product
from kitsune.search.es_utils import handle_es_errors
from kitsune.search.forms import SimpleSearchForm
from kitsune.search.search_utils import generate_simple_search
from kitsune.search.utils import clean_excerpt, locale_or_default
from kitsune.sumo.api_utils import JSONRenderer
from kitsune.sumo.json_utils import markup_json
from kitsune.sumo.templatetags.jinja_helpers import Paginator
from kitsune.sumo.utils import paginate
from kitsune.wiki.facets import documents_for

log = logging.getLogger("k.search")


EXCERPT_JOINER = pgettext_lazy("between search excerpts", "...")


def cache_control(resp, cache_period):
    """Inserts cache/expires headers"""
    resp["Cache-Control"] = "max-age=%s" % (cache_period * 60)
    resp["Expires"] = (datetime.utcnow() + timedelta(minutes=cache_period)).strftime(
        "%A, %d %B %Y %H:%M:%S GMT"
    )
    return resp


def _es_down_template(request, *args, **kwargs):
    """Returns the appropriate "Elasticsearch is down!" template"""
    return "search/down.html"


class UnknownDocType(Exception):
    """Signifies a doctype for which there's no handling"""

    pass


def build_results_list(pages, is_json):
    """Takes a paginated search and returns results List

    Handles wiki documents, questions and contributor forum posts.

    :arg pages: paginated S
    :arg is_json: whether or not this is generated results for json output

    :returns: list of dicts

    """
    results = []
    for rank, doc in enumerate(pages, pages.start_index()):
        if doc["model"] == "wiki_document":
            summary = _build_es_excerpt(doc)
            if not summary:
                summary = doc["document_summary"]
            result = {"title": doc["document_title"], "type": "document"}

        elif doc["model"] == "questions_question":
            summary = _build_es_excerpt(doc)
            if not summary:
                # We're excerpting only question_content, so if the query matched
                # question_title or question_answer_content, then there won't be any
                # question_content excerpts. In that case, just show the question--but
                # only the first 500 characters.
                summary = bleach.clean(doc["question_content"], strip=True)[:500]

            result = {
                "title": doc["question_title"],
                "type": "question",
                "last_updated": datetime.fromtimestamp(doc["updated"]),
                "is_solved": doc["question_is_solved"],
                "num_answers": doc["question_num_answers"],
                "num_votes": doc["question_num_votes"],
                "num_votes_past_week": doc["question_num_votes_past_week"],
            }

        elif doc["model"] == "forums_thread":
            summary = _build_es_excerpt(doc, first_only=True)
            result = {"title": doc["post_title"], "type": "thread"}

        else:
            raise UnknownDocType("%s is an unknown doctype" % doc["model"])

        result["url"] = doc["url"]
        if not is_json:
            result["object"] = doc
        result["search_summary"] = summary
        result["rank"] = rank
        result["score"] = doc.es_meta.score
        result["explanation"] = escape(format_explanation(doc.es_meta.explanation))
        result["id"] = doc["id"]
        results.append(result)

    return results


@markup_json
@handle_es_errors(_es_down_template)
def simple_search(request):
    """Elasticsearch-specific simple search view.

    This view is for end user searching of the Knowledge Base and
    Support Forum. Filtering options are limited to:

    * product (`product=firefox`, for example, for only Firefox results)
    * document type (`w=2`, for example, for Support Forum questions only)

    """

    to_json = JSONRenderer().render
    template = "search/results.html"

    # Build form.
    search_form = SimpleSearchForm(request.GET, auto_id=False)

    # Validate request.
    if not search_form.is_valid():
        if request.IS_JSON:
            return HttpResponse(
                json.dumps({"error": _("Invalid search data.")}),
                content_type=request.CONTENT_TYPE,
                status=400,
            )

        t = "search/form.html"
        return cache_control(
            render(request, t, {"request": request, "search_form": search_form}),
            settings.SEARCH_CACHE_PERIOD,
        )

    # Generate search.
    cleaned = search_form.cleaned_data

    language = locale_or_default(cleaned["language"] or request.LANGUAGE_CODE)
    lang_name = settings.LANGUAGES_DICT.get(language.lower()) or ""

    searcher = generate_simple_search(search_form, language, with_highlights=True)
    searcher = searcher[: settings.SEARCH_MAX_RESULTS]

    # Generate output.
    pages = paginate(request, searcher, settings.SEARCH_RESULTS_PER_PAGE)

    if pages.paginator.count == 0:
        fallback_results = _fallback_results(language, cleaned["product"])
        results = []

    else:
        fallback_results = None
        results = build_results_list(pages, request.IS_JSON)

    product = Product.objects.filter(slug__in=cleaned["product"])
    if product:
        product_titles = [pgettext("DB: products.Product.title", p.title) for p in product]
    else:
        product_titles = [_("All Products")]

    # FIXME: This is probably bad l10n.
    product_titles = ", ".join(product_titles)

    data = {
        "num_results": pages.paginator.count,
        "results": results,
        "fallback_results": fallback_results,
        "product_titles": product_titles,
        "q": cleaned["q"],
        "w": cleaned["w"],
        "lang_name": lang_name,
        "products": Product.objects.filter(visible=True),
    }

    if request.IS_JSON:
        data["total"] = len(data["results"])
        data["products"] = [{"slug": p.slug, "title": p.title} for p in data["products"]]

        if product:
            data["product"] = product[0].slug

        pages = Paginator(pages)
        data["pagination"] = dict(
            number=pages.pager.number,
            num_pages=pages.pager.paginator.num_pages,
            has_next=pages.pager.has_next(),
            has_previous=pages.pager.has_previous(),
            max=pages.max,
            span=pages.span,
            dotted_upper=pages.pager.dotted_upper,
            dotted_lower=pages.pager.dotted_lower,
            page_range=pages.pager.page_range,
            url=pages.pager.url,
        )
        if not results:
            data["message"] = constants.NO_MATCH

        json_data = to_json(data)
        if request.JSON_CALLBACK:
            json_data = request.JSON_CALLBACK + "(" + json_data + ");"
        return HttpResponse(json_data, content_type=request.CONTENT_TYPE)

    data.update({"product": product, "pages": pages, "search_form": search_form})
    resp = cache_control(render(request, template, data), settings.SEARCH_CACHE_PERIOD)
    resp.set_cookie(
        settings.LAST_SEARCH_COOKIE,
        urlquote(cleaned["q"]),
        max_age=3600,
        secure=False,
        httponly=False,
    )
    return resp


@cache_page(60 * 15)  # 15 minutes.
def opensearch_suggestions(request):
    """A simple search view that returns OpenSearch suggestions."""
    content_type = "application/x-suggestions+json"
    search_form = SimpleSearchForm(request.GET, auto_id=False)
    if not search_form.is_valid():
        return HttpResponseBadRequest(content_type=content_type)

    cleaned = search_form.cleaned_data
    language = locale_or_default(cleaned["language"] or request.LANGUAGE_CODE)
    searcher = generate_simple_search(search_form, language, with_highlights=False)
    searcher = searcher.values_dict("document_title", "question_title", "url")
    results = searcher[:10]

    def urlize(r):
        return "%s://%s%s" % (
            "https" if request.is_secure() else "http",
            request.get_host(),
            r["url"][0],
        )

    def titleize(r):
        # NB: Elasticsearch returns an array of strings as the value, so we mimic that and
        # then pull out the first (and only) string.
        return r.get("document_title", r.get("question_title", [_("No title")]))[0]

    try:
        data = [cleaned["q"], [titleize(r) for r in results], [], [urlize(r) for r in results]]
    except ES_EXCEPTIONS:
        # If we have Elasticsearch problems, we just send back an empty set of results.
        data = []

    return HttpResponse(json.dumps(data), content_type=content_type)


@cache_page(60 * 60 * 168)  # 1 week.
def opensearch_plugin(request):
    """Render an OpenSearch Plugin."""
    host = "%s://%s" % ("https" if request.is_secure() else "http", request.get_host())

    # Use `render_to_response` here instead of `render` because `render`
    # includes the request in the context of the response. Requests
    # often include the session, which can include pickable things.
    # `render_to_respones` doesn't include the request in the context.
    return render_to_response(
        "search/plugin.html",
        {"host": host, "locale": request.LANGUAGE_CODE},
        content_type="application/opensearchdescription+xml",
    )


def _ternary_filter(ternary_value):
    """Return a search query given a TERNARY_YES or TERNARY_NO.

    Behavior for TERNARY_OFF is undefined.

    """
    return ternary_value == constants.TERNARY_YES


def _build_es_excerpt(result, first_only=False):
    """Return concatenated search excerpts.

    :arg result: The result object from the queryset results
    :arg first_only: True if we should show only the first bit, False
        if we should show all bits

    """
    bits = [m.strip() for m in chain(*list(result.es_meta.highlight.values()))]

    if first_only and bits:
        excerpt = bits[0]
    else:
        excerpt = EXCERPT_JOINER.join(bits)

    return jinja2.Markup(clean_excerpt(excerpt))


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
