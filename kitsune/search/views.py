import json
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils.translation import pgettext
from django.views.decorators.cache import cache_page

from kitsune import search as constants
from kitsune.products.models import Product
from kitsune.search.base import SumoSearchPaginator
from kitsune.search.config import SEMANTIC_SEARCH_MIN_SCORE
from kitsune.search.forms import SimpleSearchForm
from kitsune.search.search import (
    CompoundSearch,
    HybridCompoundSearch,
    HybridQuestionSearch,
    HybridWikiSearch,
    QuestionSearch,
    SemanticQuestionSearch,
    SemanticWikiSearch,
    WikiSearch,
)
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


def _create_search(search_type, query, locale, product, w_flags):
    """Create appropriate search object based on search type."""

    # Map search types to their corresponding classes
    search_classes = {
        "hybrid": (HybridWikiSearch, HybridQuestionSearch, HybridCompoundSearch),
        "semantic": (SemanticWikiSearch, SemanticQuestionSearch, None),
        "traditional": (WikiSearch, QuestionSearch, None),
    }

    # Default to hybrid if not specified
    if search_type not in search_classes:
        search_type = "hybrid"

    wiki_class, question_class, compound_class = search_classes[search_type]

    # Determine which content types to search
    has_wiki = bool(w_flags & constants.WHERE_WIKI)
    has_questions = bool(w_flags & constants.WHERE_SUPPORT)

    # For hybrid search, use optimized single-type classes when possible
    if search_type == "hybrid":
        if has_wiki and has_questions:
            # Both types - use compound search
            return compound_class(query=query, locale=locale, product=product)
        elif has_wiki:
            # Wiki only - use direct wiki search
            return wiki_class(query=query, locale=locale, product=product)
        elif has_questions:
            # Questions only - use direct question search
            return question_class(query=query, locale=locale, product=product)
        else:
            # No specific flags - default to compound search
            return compound_class(query=query, locale=locale, product=product)

    # For semantic and traditional search, use CompoundSearch with appropriate classes
    else:
        search = CompoundSearch()
        if has_wiki:
            search.add(wiki_class(query=query, locale=locale, product=product))
        if has_questions:
            search.add(question_class(query=query, locale=locale, product=product))
        return search


def _execute_search_with_pagination(request, search):
    """Execute search and apply pagination."""
    page = paginate(
        request,
        search,
        per_page=settings.SEARCH_RESULTS_PER_PAGE,
        paginator_cls=SumoSearchPaginator,
    )
    return page, search.total, search.results


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

    # create search object - default to hybrid search
    search_type = cleaned.get("search_type") or request.GET.get("search_type", "hybrid")

    # Allow override to traditional search if needed
    if not getattr(settings, "USE_SEMANTIC_SEARCH", True):
        search_type = "traditional"

    try:
        search = _create_search(search_type, cleaned["q"], language, product, cleaned["w"])
        page, total, results = _execute_search_with_pagination(request, search)

        # Enhanced logging for search analysis
        log.info(f"Search '{cleaned['q']}' ({search_type}) returned {total} results")
        if results:
            scores = []
            for i, result in enumerate(results[:10]):  # Log first 10 results
                score = result.get('score', 'unknown') if isinstance(result, dict) else getattr(result, 'meta', {}).get('score', 'unknown')
                title = result.get('title', 'unknown') if isinstance(result, dict) else getattr(result, 'title', 'unknown')
                result_type = result.get('type', 'unknown') if isinstance(result, dict) else 'unknown'

                if isinstance(score, int | float):
                    scores.append(score)

                if i < 5:  # Only log details for top 5
                    log.info(f"Result {i+1}: score={score}, type={result_type}, title='{title[:50]}...'")

            # Log score distribution for analysis
            if scores:
                min_score, max_score = min(scores), max(scores)
                avg_score = sum(scores) / len(scores)
                log.info(f"Score distribution: min={min_score:.3f}, max={max_score:.3f}, avg={avg_score:.3f}, count={len(scores)}")

                # Log potential score gaps that might indicate semantic vs text results
                if len(scores) >= 2:
                    score_gaps = [abs(scores[i] - scores[i+1]) for i in range(len(scores)-1)]
                    max_gap = max(score_gaps) if score_gaps else 0
                    log.info(f"Max score gap: {max_gap:.3f} (may indicate retriever mixing)")
        else:
            log.info("No results returned from search")

        # For debugging irrelevant queries, log if we got unexpected results
        if cleaned['q'] and any(pattern in cleaned['q'].lower() for pattern in ['love', 'turtle', 'hate']):
            if total > 0:
                log.warning(f"UNEXPECTED: Query '{cleaned['q']}' (likely irrelevant) returned {total} results")
                if results:
                    max_score = max(result.get('score', 0) for result in results if isinstance(result, dict))
                    log.warning(f"Max score for irrelevant query: {max_score:.3f}")
            else:
                log.info(f"GOOD: Irrelevant query '{cleaned['q']}' correctly returned 0 results")

        # For hybrid search, check if semantic component is performing well
        # Only fallback if the query seems potentially relevant
        if search_type == "hybrid" and total > 0 and results:
            # Results are dictionaries after make_result(), so access score key directly
            try:
                max_score = max(result.get("score", 0) for result in results if isinstance(result, dict))
            except (AttributeError, TypeError, ValueError):
                # Fallback: if results are still hit objects, try accessing meta.score
                try:
                    max_score = max(result.meta.score for result in results)
                except AttributeError:
                    max_score = 1.0  # Safe default to avoid fallback

            if max_score < SEMANTIC_SEARCH_MIN_SCORE:
                log.info(f"Hybrid search max score {max_score} below threshold {SEMANTIC_SEARCH_MIN_SCORE}, falling back to traditional")
                search = _create_search("traditional", cleaned["q"], language, product, cleaned["w"])
                page, total, results = _execute_search_with_pagination(request, search)
    except Exception as e:
        log.warning(f"Hybrid search failed, falling back to traditional: {e}")
        search = _create_search("traditional", cleaned["q"], language, product, cleaned["w"])
        page, total, results = _execute_search_with_pagination(request, search)

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
