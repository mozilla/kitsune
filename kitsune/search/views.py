import json
import logging
from datetime import datetime, timedelta
from itertools import chain

import bleach
import jinja2
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.utils.html import escape
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page
from elasticutils.contrib.django import ES_EXCEPTIONS
from elasticutils.utils import format_explanation

from kitsune import search as constants
from kitsune.products.models import Product
from kitsune.search.forms import SimpleSearchForm
from kitsune.search.search_utils import generate_simple_search
from kitsune.search.utils import clean_excerpt, locale_or_default
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
