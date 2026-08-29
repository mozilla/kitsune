"""Search-specific orchestration for the authorized hybrid retrieval path."""

import hashlib
import json
import logging
import secrets
from collections.abc import Collection
from contextlib import suppress
from dataclasses import dataclass, replace
from time import perf_counter
from typing import Literal

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django_ratelimit.core import is_ratelimited

from kitsune import search as constants
from kitsune.retrieval.access import (
    AuthorizedCandidate,
    AuthorizedPassage,
    ViewerAccess,
    reauthorize_cached_candidates,
    retrieve,
    viewer_access_for,
)
from kitsune.retrieval.checks import is_valid_query_embedding_rate
from kitsune.retrieval.embeddings import EmbeddingRecipe, EmbeddingUnavailable, recipe_to_payload
from kitsune.retrieval.events import emit
from kitsune.retrieval.index import resolve_read_state
from kitsune.retrieval.query import (
    AAQ_SOURCE,
    KB_SOURCE,
    LegacyQuestion,
    RetrievalResult,
    SimilarityFloorUnavailable,
    Source,
    similarity_floor_for_meta,
)
from kitsune.retrieval.query_vectors import (
    CacheLookupOutcome,
    CacheWriteOutcome,
    embed_and_cache_query_vector,
    get_cached_query_vector,
)
from kitsune.search import SNIPPET_LENGTH
from kitsune.search.search import strip_html
from kitsune.sumo.urlresolvers import reverse

FallbackReason = Literal[
    "rate_limited",
    "rate_limit_unavailable",
    "embedding_unavailable",
    "similarity_floor_unavailable",
]
SEARCH_SESSION_PARAMETER = "search_session"
_SEARCH_SESSION_VERSION = 1


class HybridSearchSessionUnavailable(ValueError):
    """The requested continuation is missing, expired, or belongs to another search."""


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
    query_vector_cache_lookup: CacheLookupOutcome | None
    query_vector_cache_write: CacheWriteOutcome | None
    fallback_reason: FallbackReason | None
    session_token: str | None


@dataclass(frozen=True)
class _HybridSearchSession:
    version: int
    fingerprint: str
    result: RetrievalResult[AuthorizedCandidate]
    page_ends: tuple[int, ...]
    seen_family_ids: tuple[str, ...]
    query_vector: tuple[float, ...] | None
    similarity_floor: float | None
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


def _session_cache_key(token: str) -> str:
    digest = hashlib.sha256(token.encode()).hexdigest()
    return f"retrieval:search-session:v{_SEARCH_SESSION_VERSION}:{digest}"


def _load_search_session(token: str, fingerprint: str) -> _HybridSearchSession | None:
    if not isinstance(token, str) or not 20 <= len(token) <= 128:
        return None
    try:
        state = cache.get(_session_cache_key(token))
    except Exception:
        with suppress(Exception):
            emit(
                "retrieval.query.degraded",
                level=logging.WARNING,
                reason="search_session_cache_read_failed",
            )
        return None
    if (
        not isinstance(state, _HybridSearchSession)
        or state.version != _SEARCH_SESSION_VERSION
        or state.fingerprint != fingerprint
    ):
        return None
    return state


def _store_search_session(token: str, state: _HybridSearchSession) -> bool:
    try:
        outcome = cache.set(
            _session_cache_key(token),
            state,
            timeout=settings.RETRIEVAL_SEARCH_SESSION_TTL_SECONDS,
        )
    except Exception:
        outcome = False
    if outcome is False:
        with suppress(Exception):
            emit(
                "retrieval.query.degraded",
                level=logging.WARNING,
                reason="search_session_cache_write_failed",
            )
        return False
    return True


def _refresh_search_session(token: str) -> bool:
    try:
        outcome = cache.touch(
            _session_cache_key(token),
            timeout=settings.RETRIEVAL_SEARCH_SESSION_TTL_SECONDS,
        )
    except Exception:
        outcome = False
    if not outcome:
        with suppress(Exception):
            emit(
                "retrieval.query.degraded",
                level=logging.WARNING,
                reason="search_session_cache_write_failed",
            )
        return False
    return True


def _search_fingerprint(
    *,
    query: str,
    locale: str,
    sources: Collection[Source],
    product_id: int | None,
    viewer_access: ViewerAccess,
    kb_index: str | None,
    recipe: EmbeddingRecipe | None,
) -> str:
    payload = {
        "query": query,
        "locale": locale,
        "sources": sorted(sources),
        "product_id": product_id,
        "viewer_access": {
            "group_ids": viewer_access.group_ids,
            "privileged": viewer_access.privileged,
        },
        "kb_index": kb_index,
        "recipe": recipe_to_payload(recipe) if recipe is not None else None,
        "ranking": {
            "semantic_k": settings.RETRIEVAL_SEMANTIC_K,
            "num_candidates": settings.RETRIEVAL_KNN_NUM_CANDIDATES,
            "rank_window_size": settings.RETRIEVAL_RRF_RANK_WINDOW_SIZE,
            "segment_size": settings.RETRIEVAL_SEARCH_SEGMENT_SIZE,
            "results_per_page": settings.SEARCH_RESULTS_PER_PAGE,
            "locale_composition": settings.RETRIEVAL_LOCALE_COMPOSITION,
            "default_operator": settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR,
            "minimum_should_match": settings.RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH,
            "similarity_floors": settings.RETRIEVAL_KNN_SIMILARITY_FLOORS,
        },
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _retrieve_segment(
    query: str,
    *,
    viewer_access: ViewerAccess,
    kb_index: str | None,
    locale: str,
    sources: Collection[Source],
    product_id: int | None,
    query_vector: tuple[float, ...] | None,
    similarity_floor: float | None,
    excluded_family_ids: Collection[str],
) -> RetrievalResult[AuthorizedCandidate]:
    return retrieve(
        query,
        viewer_access=viewer_access,
        kb_index=kb_index,
        locale=locale,
        sources=sources,
        product_id=product_id,
        query_vector=query_vector,
        similarity_floor=similarity_floor,
        semantic_k=settings.RETRIEVAL_SEMANTIC_K,
        num_candidates=settings.RETRIEVAL_KNN_NUM_CANDIDATES,
        rank_window_size=settings.RETRIEVAL_RRF_RANK_WINDOW_SIZE,
        locale_composition=settings.RETRIEVAL_LOCALE_COMPOSITION,
        page_size=settings.RETRIEVAL_SEARCH_SEGMENT_SIZE,
        default_operator=settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR,
        minimum_should_match=(
            settings.RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH
            if settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR == "OR"
            else None
        ),
        excluded_family_ids=excluded_family_ids,
    )


def _append_segment(
    state: _HybridSearchSession | None,
    segment: RetrievalResult[AuthorizedCandidate],
    *,
    fingerprint: str,
    query_vector: tuple[float, ...] | None,
    similarity_floor: float | None,
    fallback_reason: FallbackReason | None,
) -> _HybridSearchSession:
    existing_candidates = state.result.candidates if state else ()
    existing_families = {candidate.family_id for candidate in existing_candidates}
    unique_candidates = []
    segment_families = set(existing_families)
    for candidate in segment.candidates:
        if candidate.family_id not in segment_families:
            unique_candidates.append(candidate)
            segment_families.add(candidate.family_id)
    appended = tuple(
        replace(candidate, rank=len(existing_candidates) + rank)
        for rank, candidate in enumerate(unique_candidates, start=1)
    )
    old_page_ends = state.page_ends if state else ()
    new_page_ends = tuple(
        len(existing_candidates) + min(end, len(appended))
        for end in range(
            settings.SEARCH_RESULTS_PER_PAGE,
            len(appended) + settings.SEARCH_RESULTS_PER_PAGE,
            settings.SEARCH_RESULTS_PER_PAGE,
        )
    )
    encountered = segment.encountered_family_ids or tuple(
        candidate.family_id for candidate in segment.candidates
    )
    old_seen = state.seen_family_ids if state else ()
    seen_set = set(old_seen)
    new_seen = tuple(
        family_id
        for family_id in dict.fromkeys(encountered)
        if family_id not in seen_set
    )
    seen = (*old_seen, *new_seen)
    made_progress = bool(new_seen)

    if state is None:
        combined = replace(
            segment,
            candidates=appended,
            encountered_family_ids=seen,
            has_more=segment.has_more and made_progress,
        )
    else:
        combined = RetrievalResult(
            candidates=(*existing_candidates, *appended),
            approximate_total=max(
                state.result.approximate_total,
                len(old_seen) + segment.approximate_total,
                len(seen),
            ),
            has_more=segment.has_more and made_progress,
            mode=state.result.mode,
            degraded=state.result.degraded or segment.degraded,
            failed_shards=max(state.result.failed_shards, segment.failed_shards),
            took_ms=segment.took_ms,
            encountered_family_ids=seen,
            invalid_hit_count=(
                state.result.invalid_hit_count + segment.invalid_hit_count
            ),
            authorization_rejection_count=(
                state.result.authorization_rejection_count
                + segment.authorization_rejection_count
            ),
            db_ms=segment.db_ms,
        )
    return _HybridSearchSession(
        version=_SEARCH_SESSION_VERSION,
        fingerprint=fingerprint,
        result=combined,
        page_ends=(*old_page_ends, *new_page_ends),
        seen_family_ids=seen,
        query_vector=query_vector,
        similarity_floor=similarity_floor,
        fallback_reason=fallback_reason,
    )


def run_hybrid_search(
    request: HttpRequest,
    *,
    query: str,
    locale: str,
    sources: Collection[Source],
    product_id: int | None,
    page: int,
    session_token: str | None = None,
) -> HybridSearchResults:
    """Return one page from a pinned, incrementally extended hybrid ranking."""
    started = perf_counter()
    phase = "access"
    try:
        source_set = frozenset(sources)
        access_started = perf_counter()
        viewer_access = viewer_access_for(request.user)
        db_ms = round((perf_counter() - access_started) * 1000)
        kb_index = None
        recipe = None
        meta = None
        query_vector: tuple[float, ...] | None = None
        similarity_floor = None
        embedding_ms = None
        cache_lookup: CacheLookupOutcome | None = None
        cache_write: CacheWriteOutcome | None = None
        fallback_reason: FallbackReason | None = None

        if KB_SOURCE in source_set:
            phase = "index_resolution"
            kb_index, recipe, meta = resolve_read_state()

        fingerprint = _search_fingerprint(
            query=query,
            locale=locale,
            sources=source_set,
            product_id=product_id,
            viewer_access=viewer_access,
            kb_index=kb_index,
            recipe=recipe,
        )
        state = None
        state_changed = False
        if session_token:
            phase = "session_cache"
            state = _load_search_session(session_token, fingerprint)
            if state is None:
                raise HybridSearchSessionUnavailable("search continuation is unavailable")
            query_vector = state.query_vector
            similarity_floor = state.similarity_floor
            fallback_reason = state.fallback_reason

        if state is None and KB_SOURCE in source_set:
            phase = "similarity_floor"
            try:
                assert meta is not None
                similarity_floor = similarity_floor_for_meta(meta)
            except SimilarityFloorUnavailable:
                # No floor for the active profile means no bounded kNN; search stays available.
                fallback_reason = "similarity_floor_unavailable"
                emit("retrieval.query.degraded", level=logging.WARNING, reason=fallback_reason)
            else:
                phase = "cache"
                assert recipe is not None
                cached_vector, cache_lookup = get_cached_query_vector(query, recipe)
                query_vector = tuple(cached_vector) if cached_vector is not None else None
                if cached_vector is None:
                    phase = "rate_limit"
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
                        phase = "embedding"
                        embedding_started = perf_counter()
                        try:
                            assert recipe is not None
                            embedded_vector, cache_write = embed_and_cache_query_vector(
                                query, recipe
                            )
                            query_vector = tuple(embedded_vector)
                        except EmbeddingUnavailable:
                            fallback_reason = "embedding_unavailable"
                        finally:
                            embedding_ms = round((perf_counter() - embedding_started) * 1000)

        es_took_ms = 0
        if state is None:
            phase = "retrieval"
            segment = _retrieve_segment(
                query,
                viewer_access=viewer_access,
                kb_index=kb_index,
                locale=locale,
                sources=source_set,
                product_id=product_id,
                query_vector=query_vector,
                similarity_floor=similarity_floor,
                excluded_family_ids=(),
            )
            es_took_ms += segment.took_ms
            db_ms += segment.db_ms
            state = _append_segment(
                None,
                segment,
                fingerprint=fingerprint,
                query_vector=query_vector,
                similarity_floor=similarity_floor,
                fallback_reason=fallback_reason,
            )
            state_changed = True

        available_pages = len(state.page_ends)
        page = min(max(page, 1), max(available_pages, 1) + int(state.result.has_more))
        if page > available_pages and state.result.has_more:
            phase = "retrieval"
            segment = _retrieve_segment(
                query,
                viewer_access=viewer_access,
                kb_index=kb_index,
                locale=locale,
                sources=source_set,
                product_id=product_id,
                query_vector=state.query_vector,
                similarity_floor=state.similarity_floor,
                excluded_family_ids=state.seen_family_ids,
            )
            es_took_ms += segment.took_ms
            db_ms += segment.db_ms
            state = _append_segment(
                state,
                segment,
                fingerprint=fingerprint,
                query_vector=state.query_vector,
                similarity_floor=state.similarity_floor,
                fallback_reason=state.fallback_reason,
            )
            state_changed = True

        available_pages = len(state.page_ends)
        page = min(page, max(available_pages, 1))

        needs_session = bool(session_token) or available_pages > 1 or state.result.has_more
        token = None
        session_cache_failed = False
        if needs_session:
            session_cache_token = session_token or secrets.token_urlsafe(24)
            stored = (
                _store_search_session(session_cache_token, state)
                if state_changed or not session_token
                else _refresh_search_session(session_cache_token)
            )
            token = session_cache_token if stored else None
            session_cache_failed = not stored

        if available_pages:
            page_start = state.page_ends[page - 2] if page > 1 else 0
            page_end = state.page_ends[page - 1]
        else:
            page_start = page_end = 0
        has_next = page < available_pages or state.result.has_more
        if token is None:
            has_next = False
        cached_page = replace(
            state.result,
            candidates=state.result.candidates[page_start:page_end],
            approximate_total=(
                len(state.result.candidates)
                if session_cache_failed
                else state.result.approximate_total
            ),
            has_more=has_next,
            took_ms=es_took_ms,
        )
        phase = "authorization"
        result = reauthorize_cached_candidates(
            cached_page,
            viewer_access=viewer_access,
            locale=locale,
            product_id=product_id,
        )
        db_ms += result.db_ms
        phase = "presentation"
        presented = tuple(
            result_from_candidate(candidate, locale) for candidate in result.candidates
        )
        total_ms = round((perf_counter() - started) * 1000)
        response = HybridSearchResults(
            results=presented,
            approximate_total=(
                len(result.candidates) if session_cache_failed else result.approximate_total
            ),
            page=page,
            has_previous=page > 1 and token is not None,
            has_next=has_next,
            mode=result.mode,
            degraded=result.degraded,
            failed_shards=result.failed_shards,
            es_took_ms=es_took_ms,
            total_ms=total_ms,
            embedding_ms=embedding_ms,
            query_vector_cache_lookup=cache_lookup,
            query_vector_cache_write=cache_write,
            fallback_reason=fallback_reason,
            session_token=token,
        )
    except HybridSearchSessionUnavailable:
        raise
    except Exception as exc:
        # Observability must never replace the failure the request actually encountered.
        with suppress(Exception):
            emit(
                "retrieval.query.failed",
                level=logging.ERROR,
                phase=phase,
                error_type=type(exc).__name__,
                total_ms=round((perf_counter() - started) * 1000),
            )
        raise

    # Search results remain usable even if structured logging is unavailable.
    with suppress(Exception):
        emit(
            "retrieval.query.completed",
            outcome=(
                "degraded" if result.degraded else "fallback" if fallback_reason else "success"
            ),
            mode=result.mode,
            kb_result_count=sum(item["type"] == "document" for item in presented),
            aaq_result_count=sum(item["type"] == "question" for item in presented),
            invalid_hit_count=result.invalid_hit_count,
            authorization_rejection_count=result.authorization_rejection_count,
            failed_shard_count=result.failed_shards,
            requested_locale=locale,
            locale_fallback_count=sum(bool(item["locale_fallback"]) for item in presented),
            cache_lookup=cache_lookup,
            cache_write=cache_write,
            fallback_reason=fallback_reason,
            total_ms=total_ms,
            embedding_ms=embedding_ms,
            es_ms=es_took_ms,
            db_ms=db_ms,
        )
    return response


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
