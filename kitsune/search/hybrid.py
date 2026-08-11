"""Search-specific orchestration for the authorized hybrid retrieval path."""

from collections.abc import Collection
from dataclasses import dataclass
from functools import lru_cache
from time import perf_counter
from typing import Literal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django_ratelimit.core import is_ratelimited

from kitsune import search as constants
from kitsune.retrieval.access import (
    AuthorizedCandidate,
    AuthorizedPassage,
    retrieve,
    viewer_access_for,
)
from kitsune.retrieval.checks import is_valid_query_embedding_rate
from kitsune.retrieval.embeddings import EmbeddingUnavailable
from kitsune.retrieval.index import resolve_read_target_and_recipe
from kitsune.retrieval.query import (
    AAQ_SOURCE,
    KB_SOURCE,
    LegacyQuestion,
    Source,
    similarity_floor_for_index,
)
from kitsune.retrieval.query_vectors import (
    embed_and_cache_query_vector,
    get_cached_query_vector,
)
from kitsune.search import SNIPPET_LENGTH
from kitsune.search.search import strip_html
from kitsune.sumo.urlresolvers import reverse

FallbackReason = Literal["rate_limited", "rate_limit_unavailable", "embedding_unavailable"]


@dataclass(frozen=True)
class HybridSearchResults:
    results: tuple[dict, ...]
    approximate_total: int
    page: int
    has_previous: bool
    has_next: bool
    mode: Literal["lexical", "hybrid"]
    degraded: bool
    failed_shards: int
    es_took_ms: int
    total_ms: int
    embedding_ms: int | None
    query_vector_cache_hit: bool | None
    fallback_reason: FallbackReason | None


def sources_for_where(where: int) -> frozenset[Source]:
    """Map the three existing public search tabs to explicit retrieval sources."""
    match where:
        case constants.WHERE_WIKI:
            return frozenset({KB_SOURCE})
        case constants.WHERE_SUPPORT:
            return frozenset({AAQ_SOURCE})
        case constants.WHERE_BASIC:
            return frozenset({KB_SOURCE, AAQ_SOURCE})
        case _:
            raise ValueError("hybrid search supports KB, AAQ, or both")


def run_hybrid_search(
    request: HttpRequest,
    *,
    query: str,
    locale: str,
    sources: Collection[Source],
    product_id: int | None,
    page: int,
) -> HybridSearchResults:
    """Run one bounded retrieval request and return current search-result dictionaries."""
    started = perf_counter()
    source_set = frozenset(sources)
    viewer_access = viewer_access_for(request.user)
    kb_index = None
    query_vector = None
    similarity_floor = None
    embedding_ms = None
    cache_hit = None
    fallback_reason: FallbackReason | None = None

    if KB_SOURCE in source_set:
        kb_index, recipe = resolve_read_target_and_recipe()
        query_vector = get_cached_query_vector(query, recipe)
        cache_hit = query_vector is not None
        if query_vector is None:
            rate = settings.RETRIEVAL_QUERY_EMBEDDING_RATE
            if not is_valid_query_embedding_rate(rate):
                raise ImproperlyConfigured("RETRIEVAL_QUERY_EMBEDDING_RATE is invalid")

            limited = rate.startswith("0/")
            if not limited:
                try:
                    limited = is_ratelimited(
                        request,
                        group="retrieval-query-embedding",
                        key="user_or_ip",
                        rate=rate,
                        increment=True,
                    )
                except Exception:
                    limited = True
                    fallback_reason = "rate_limit_unavailable"

            if limited:
                fallback_reason = fallback_reason or "rate_limited"
            else:
                similarity_floor = cached_similarity_floor(kb_index)
                embedding_started = perf_counter()
                try:
                    query_vector = embed_and_cache_query_vector(query, recipe)
                except EmbeddingUnavailable:
                    fallback_reason = "embedding_unavailable"
                finally:
                    embedding_ms = round((perf_counter() - embedding_started) * 1000)
        else:
            similarity_floor = cached_similarity_floor(kb_index)

    result = retrieve(
        query,
        viewer_access=viewer_access,
        kb_index=kb_index,
        locale=locale,
        sources=source_set,
        product_id=product_id,
        query_vector=query_vector,
        similarity_floor=similarity_floor,
        semantic_k=settings.RETRIEVAL_SEMANTIC_K,
        num_candidates=settings.RETRIEVAL_KNN_NUM_CANDIDATES,
        rank_window_size=settings.RETRIEVAL_RRF_RANK_WINDOW_SIZE,
        locale_composition=settings.RETRIEVAL_LOCALE_COMPOSITION,
        page_size=settings.SEARCH_RESULTS_PER_PAGE,
        authorization_overfetch=settings.RETRIEVAL_AUTHORIZATION_OVERFETCH,
        offset=(page - 1) * settings.SEARCH_RESULTS_PER_PAGE,
        max_offset=settings.RETRIEVAL_MAX_PAGE_OFFSET,
        default_operator=settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR,
        minimum_should_match=(
            settings.RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH
            if settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR == "OR"
            else None
        ),
    )
    return HybridSearchResults(
        results=tuple(result_from_candidate(candidate, locale) for candidate in result.candidates),
        approximate_total=result.approximate_total,
        page=page,
        has_previous=page > 1,
        has_next=result.has_more,
        mode=result.mode,
        degraded=result.degraded,
        failed_shards=result.failed_shards,
        es_took_ms=result.took_ms,
        total_ms=round((perf_counter() - started) * 1000),
        embedding_ms=embedding_ms,
        query_vector_cache_hit=cache_hit,
        fallback_reason=fallback_reason,
    )


@lru_cache(maxsize=8)
def cached_similarity_floor(index: str) -> float:
    """Cache immutable physical-index similarity metadata within this process."""
    return similarity_floor_for_index(index)


def result_from_candidate(candidate: AuthorizedCandidate, requested_locale: str) -> dict:
    """Convert authorized evidence to the existing search presentation shape."""
    match candidate.evidence:
        case AuthorizedPassage(passage=passage, display=display):
            same_locale = passage.locale == display.locale
            if same_locale and not passage.scope and passage.body_highlight is not None:
                summary = strip_html(passage.body_highlight.text)
            elif same_locale and passage.summary_highlight is not None:
                summary = strip_html(passage.summary_highlight.text)
            elif same_locale and not passage.scope and "semantic" in passage.provenance:
                summary = strip_html(passage.text[:SNIPPET_LENGTH])
            else:
                summary = strip_html(display.summary[:SNIPPET_LENGTH])

            return {
                "type": "document",
                "url": reverse("wiki.document", args=[display.slug], locale=display.locale),
                "title": display.title,
                "search_summary": summary,
                "id": display.document_id,
                "rank": candidate.rank,
                "evidence_locale": passage.locale,
                "display_locale": display.locale,
                "locale_fallback": display.locale != requested_locale,
            }
        case LegacyQuestion() as question:
            summary = (
                strip_html(question.highlight.text)
                if question.highlight is not None
                else strip_html(question.content[:SNIPPET_LENGTH])
            )
            return {
                "type": "question",
                "url": reverse(
                    "questions.details",
                    kwargs={"question_id": question.question_id},
                ),
                "title": question.title,
                "search_summary": summary,
                "last_updated": question.updated,
                "is_solved": question.is_solved,
                "num_answers": question.num_answers,
                "num_votes": question.num_votes,
                "rank": candidate.rank,
                "evidence_locale": question.locale,
                "display_locale": question.locale,
                "locale_fallback": False,
            }
        case _:
            raise TypeError("unsupported authorized evidence")
