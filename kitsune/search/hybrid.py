"""Search-specific orchestration for the authorized hybrid retrieval path."""

import logging
from collections.abc import Collection
from contextlib import suppress
from dataclasses import dataclass
from time import perf_counter
from typing import Literal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.utils.translation import gettext as _
from django_ratelimit.core import is_ratelimited

from kitsune import search as constants
from kitsune.retrieval.access import (
    AuthorizedCandidate,
    AuthorizedPassage,
    ViewerAccess,
    retrieve,
    viewer_access_for,
)
from kitsune.retrieval.checks import is_valid_query_embedding_rate
from kitsune.retrieval.embeddings import EmbeddingUnavailable
from kitsune.retrieval.events import emit
from kitsune.retrieval.index import resolve_read_state
from kitsune.retrieval.query import (
    AAQ_SOURCE,
    KB_SOURCE,
    LegacyQuestion,
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
from kitsune.search.parser import is_plain_text_query
from kitsune.search.search import strip_html
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.managers import effective_group_ids
from kitsune.wiki.models import Audience, Document

PRIVATE_BLOCK_SIZE = 3

FallbackReason = Literal[
    "rate_limited",
    "rate_limit_unavailable",
    "embedding_unavailable",
    "similarity_floor_unavailable",
]


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
    private_block: tuple[dict, ...] = ()
    private_block_heading: str | None = None
    private_block_count: int = 0


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
    knowledge_base: Audience | None = None,
    with_private_block: bool = False,
) -> HybridSearchResults:
    """
    Run one bounded retrieval request, two with "with_private_block", and return current
    search-result dictionaries. A knowledge base limits the search to its articles.
    "with_private_block" adds a block of the viewer's top restricted articles, which the main
    results exclude on every page.
    """
    started = perf_counter()
    phase = "access"
    try:
        source_set = frozenset(sources)
        if knowledge_base is not None and source_set != {KB_SOURCE}:
            raise ValueError("a knowledge base search covers KB sources only")
        access_started = perf_counter()
        viewer_access = viewer_access_for(request.user)
        included_family_ids = None
        if knowledge_base is not None:
            included_family_ids = tuple(
                f"{KB_SOURCE}:{document_id}"
                for document_id in Document.objects.filter(
                    parent=None, audiences=knowledge_base
                ).values_list("id", flat=True)
            )
        db_ms = round((perf_counter() - access_started) * 1000)
        kb_index = None
        query_vector = None
        similarity_floor = None
        embedding_ms = None
        cache_lookup: CacheLookupOutcome | None = None
        cache_write: CacheWriteOutcome | None = None
        fallback_reason: FallbackReason | None = None

        if KB_SOURCE in source_set:
            phase = "index_resolution"
            kb_index, recipe, meta = resolve_read_state()
            # Advanced syntax (operators or quoted phrases) is an explicit lexical
            # contract; semantic retrieval would broaden results past it, so those
            # queries never acquire a query vector (mozilla/sumo#3307).
            if is_plain_text_query(query):
                phase = "similarity_floor"
                try:
                    similarity_floor = similarity_floor_for_meta(meta)
                except SimilarityFloorUnavailable:
                    # No floor for the active profile means no bounded kNN; stay lexical.
                    fallback_reason = "similarity_floor_unavailable"
                    emit(
                        "retrieval.query.degraded",
                        level=logging.WARNING,
                        reason=fallback_reason,
                    )
                else:
                    phase = "cache"
                    query_vector, cache_lookup = get_cached_query_vector(query, recipe)
                    if query_vector is None:
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
                                query_vector, cache_write = embed_and_cache_query_vector(
                                    query, recipe
                                )
                            except EmbeddingUnavailable:
                                fallback_reason = "embedding_unavailable"
                            finally:
                                embedding_ms = round((perf_counter() - embedding_started) * 1000)

        retrieval_options = {
            "kb_index": kb_index,
            "locale": locale,
            "product_id": product_id,
            "query_vector": query_vector,
            "similarity_floor": similarity_floor,
            "semantic_k": settings.RETRIEVAL_SEMANTIC_K,
            "num_candidates": settings.RETRIEVAL_KNN_NUM_CANDIDATES,
            "rank_window_size": settings.RETRIEVAL_RRF_RANK_WINDOW_SIZE,
            "locale_composition": settings.RETRIEVAL_LOCALE_COMPOSITION,
            "authorization_overfetch": settings.RETRIEVAL_AUTHORIZATION_OVERFETCH,
            "max_offset": settings.RETRIEVAL_MAX_PAGE_OFFSET,
            "default_operator": settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR,
            "minimum_should_match": (
                settings.RETRIEVAL_LEXICAL_MINIMUM_SHOULD_MATCH
                if settings.RETRIEVAL_LEXICAL_DEFAULT_OPERATOR == "OR"
                else None
            ),
        }
        retrievals = []
        block_candidates: tuple[AuthorizedCandidate, ...] = ()
        if with_private_block and knowledge_base is None and KB_SOURCE in source_set:
            phase = "private_block"
            # Membership without the Staff bypass, so Staff see only their own KBs here.
            block = retrieve(
                query,
                viewer_access=ViewerAccess(tuple(sorted(effective_group_ids(request.user)))),
                sources=frozenset({KB_SOURCE}),
                page_size=PRIVATE_BLOCK_SIZE,
                offset=0,
                restricted_only=True,
                **retrieval_options,
            )
            retrievals.append(block)
            block_candidates = block.candidates

        phase = "retrieval"
        result = retrieve(
            query,
            viewer_access=viewer_access,
            sources=source_set,
            page_size=settings.SEARCH_RESULTS_PER_PAGE,
            offset=(page - 1) * settings.SEARCH_RESULTS_PER_PAGE,
            excluded_family_ids=tuple(candidate.family_id for candidate in block_candidates),
            included_family_ids=included_family_ids,
            **retrieval_options,
        )
        retrievals.append(result)
        db_ms += sum(retrieval.db_ms for retrieval in retrievals)

        phase = "presentation"
        # The block runs on every page to keep the exclusion stable, but shows on the first.
        private_block_count = len(block_candidates)
        if page > 1:
            block_candidates = ()
        tags_started = perf_counter()
        tags = _knowledge_base_tags(request.user, (*block_candidates, *result.candidates))
        db_ms += round((perf_counter() - tags_started) * 1000)
        presented = tuple(
            result_from_candidate(candidate, locale, tags.get(candidate.family_id, ()))
            for candidate in result.candidates
        )
        private_block = tuple(
            result_from_candidate(candidate, locale, tags.get(candidate.family_id, ()))
            for candidate in block_candidates
        )
        private_block_heading = None
        if private_block:
            private_kbs = [
                {(kb["slug"], kb["name"]) for kb in item["knowledge_bases"] if kb["is_private"]}
                for item in private_block
            ]
            shared = set.intersection(*private_kbs)
            private_block_heading = (
                # L10n: %(name)s is the name of a knowledge base.
                _("From %(name)s") % {"name": shared.pop()[1]}
                if len(shared) == 1
                else _("From your knowledge bases")
            )

        degraded = any(retrieval.degraded for retrieval in retrievals)
        failed_shards = sum(retrieval.failed_shards for retrieval in retrievals)
        es_ms = sum(retrieval.took_ms for retrieval in retrievals)
        total_ms = round((perf_counter() - started) * 1000)
        response = HybridSearchResults(
            results=presented,
            approximate_total=result.approximate_total,
            page=page,
            has_previous=page > 1,
            has_next=result.has_more,
            mode=result.mode,
            degraded=degraded,
            failed_shards=failed_shards,
            es_took_ms=es_ms,
            total_ms=total_ms,
            embedding_ms=embedding_ms,
            query_vector_cache_lookup=cache_lookup,
            query_vector_cache_write=cache_write,
            fallback_reason=fallback_reason,
            private_block=private_block,
            private_block_heading=private_block_heading,
            private_block_count=private_block_count,
        )
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

    # The private block is part of this search: one event covers its work and shown results.
    shown = (*private_block, *presented)
    # Search results remain usable even if structured logging is unavailable.
    with suppress(Exception):
        emit(
            "retrieval.query.completed",
            outcome=("degraded" if degraded else "fallback" if fallback_reason else "success"),
            mode=result.mode,
            kb_result_count=sum(item["type"] == "document" for item in shown),
            aaq_result_count=sum(item["type"] == "question" for item in shown),
            invalid_hit_count=sum(retrieval.invalid_hit_count for retrieval in retrievals),
            authorization_rejection_count=sum(
                retrieval.authorization_rejection_count for retrieval in retrievals
            ),
            failed_shard_count=failed_shards,
            requested_locale=locale,
            locale_fallback_count=sum(bool(item["locale_fallback"]) for item in shown),
            cache_lookup=cache_lookup,
            cache_write=cache_write,
            fallback_reason=fallback_reason,
            total_ms=total_ms,
            embedding_ms=embedding_ms,
            es_ms=es_ms,
            db_ms=db_ms,
        )
    return response


def _knowledge_base_tags(user, candidates: Collection[AuthorizedCandidate]) -> dict[str, list]:
    """
    Map each KB family among the candidates to the KBs of its original that the user can
    read (the default KB is never one), in listing order, with one query.
    """
    family_ids = {
        candidate.family_id
        for candidate in candidates
        if isinstance(candidate.evidence, AuthorizedPassage)
    }
    tags: dict[str, list] = {family_id: [] for family_id in family_ids}
    if family_ids:
        originals = [int(family_id.removeprefix(f"{KB_SOURCE}:")) for family_id in family_ids]
        for document_id, slug, name, is_public in (
            Audience.objects.browsable_by(user)
            .filter(documents__id__in=originals)
            .values_list("documents", "slug", "name", "is_public")
        ):
            tags[f"{KB_SOURCE}:{document_id}"].append(
                {"slug": slug, "name": name, "is_private": not is_public}
            )
    return tags


def result_from_candidate(
    candidate: AuthorizedCandidate, requested_locale: str, knowledge_bases: Collection[dict] = ()
) -> dict:
    """
    Convert authorized evidence to the existing search presentation shape. KB results carry
    the given knowledge base tags; questions have none.
    """
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
                "knowledge_bases": list(knowledge_bases),
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
