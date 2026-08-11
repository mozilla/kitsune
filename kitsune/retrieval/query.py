import logging
import math
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from elasticsearch.dsl import Q as DSLQ
from elasticsearch.dsl.query import Query
from pyparsing import ParseException

from kitsune.retrieval.events import emit
from kitsune.retrieval.fingerprints import (
    SCOPE_ENVELOPE_VERSION,
    is_valid_similarity_floor,
    read_index_meta,
    similarity_profile_fingerprint,
)
from kitsune.retrieval.index import (
    CHUNK_KIND,
    PUBLIC_VISIBILITY,
    RESTRICTED_VISIBILITY,
    SIMILARITY,
)
from kitsune.search import HIGHLIGHT_TAG, SNIPPET_LENGTH
from kitsune.search.documents import QuestionDocument
from kitsune.search.es_utils import es_client
from kitsune.search.parser import Parser
from kitsune.search.parser.tokens import BaseToken, TermToken
from kitsune.search.search import (
    FVH_HIGHLIGHT_OPTIONS,
    QuestionSearch,
    WikiSearch,
    build_question_search_query,
)

KB_SOURCE: Literal["kb"] = "kb"
AAQ_SOURCE: Literal["aaq"] = "aaq"
ENGLISH_LOCALE = "en-US"

Source = Literal["kb", "aaq"]
DefaultOperator = Literal["AND", "OR"]
LocaleComposition = Literal["combined", "separate"]
RetrievalMode = Literal["lexical", "hybrid"]
RetrievalProvenance = Literal["lexical", "semantic"]
_SOURCES = frozenset({KB_SOURCE, AAQ_SOURCE})
RRF_RANK_CONSTANT = 60


class SimilarityFloorUnavailable(ImproperlyConfigured):
    """The selected index has no valid environment-specific semantic floor."""


class InvalidRetrievalResponse(ValueError):
    """Elasticsearch returned evidence that cannot cross the retrieval boundary."""


def parse_positive_integer_id(value: object) -> int | None:
    """Return a canonical positive ASCII integer ID, or None."""
    if not isinstance(value, str) or not value.isascii() or not value.isdecimal():
        return None
    parsed = int(value)
    return parsed if parsed > 0 and str(parsed) == value else None


@dataclass(frozen=True)
class LexicalClauses:
    kb_requested: Query | None
    kb_english: Query | None
    aaq_requested: Query | None


@dataclass(frozen=True)
class HighlightFragment:
    field: str
    locale: str
    text: str


@dataclass(frozen=True)
class RetrievalPassage:
    content_type: str
    object_id: str
    family_id: str
    locale: str
    position: int
    heading_path: str
    scope: tuple[frozenset[str], ...]
    text: str
    provenance: frozenset[RetrievalProvenance]
    body_highlight: HighlightFragment | None
    summary_highlight: HighlightFragment | None
    product_ids: tuple[str, ...]
    topic_ids: tuple[str, ...]
    category: str


@dataclass(frozen=True)
class LegacyQuestion:
    question_id: str
    family_id: str
    locale: str
    title: str
    content: str
    updated: datetime
    is_solved: bool
    num_answers: int
    num_votes: int
    provenance: frozenset[RetrievalProvenance]
    highlight: HighlightFragment | None


@dataclass(frozen=True)
class UnvalidatedCandidate:
    rank: int
    score: float
    family_id: str
    evidence: RetrievalPassage | LegacyQuestion


@dataclass(frozen=True)
class RetrievalResult[Candidate]:
    candidates: tuple[Candidate, ...]
    approximate_total: int
    has_more: bool
    mode: RetrievalMode
    degraded: bool
    failed_shards: int
    took_ms: int


def _render(
    parsed: BaseToken,
    *,
    fields: list[str],
    settings: dict,
    default_operator: DefaultOperator,
    minimum_should_match: str | None,
) -> Query:
    return parsed.elastic_query(
        {
            "fields": fields,
            "settings": settings,
            "default_operator": default_operator,
            "minimum_should_match": minimum_should_match,
        }
    )


def _kb_clause(
    parsed: BaseToken,
    *,
    locale: str,
    product_id: int | None,
    viewer_group_ids: Sequence[int],
    privileged: bool,
    default_operator: DefaultOperator,
    minimum_should_match: str | None,
) -> Query:
    search = WikiSearch(locale=locale)
    settings = search.get_settings()
    settings["field_mappings"]["content"] = f"content_text.{locale}"
    lexical_query = _render(
        parsed,
        fields=[
            f"keywords.{locale}^8",
            f"title.{locale}^6",
            f"summary.{locale}^4",
            f"content_text.{locale}^2",
        ],
        settings=settings,
        default_operator=default_operator,
        minimum_should_match=minimum_should_match,
    )

    filters = _kb_filters(
        locales=[locale],
        product_id=product_id,
        viewer_group_ids=viewer_group_ids,
        privileged=privileged,
    )
    return DSLQ("bool", _name=f"lexical:{KB_SOURCE}:{locale}", filter=filters, must=lexical_query)


def _kb_filters(
    *,
    locales: Sequence[str],
    product_id: int | None,
    viewer_group_ids: Sequence[int],
    privileged: bool,
) -> list[Query]:
    if isinstance(viewer_group_ids, str | bytes) or any(
        not isinstance(group_id, int) or isinstance(group_id, bool) or group_id <= 0
        for group_id in viewer_group_ids
    ):
        raise ValueError("viewer_group_ids must contain only positive integers")

    public = DSLQ("term", visibility=PUBLIC_VISIBILITY)
    if privileged:
        access = DSLQ("terms", visibility=[PUBLIC_VISIBILITY, RESTRICTED_VISIBILITY])
    elif viewer_group_ids:
        access = DSLQ(
            "bool",
            should=[
                public,
                DSLQ(
                    "bool",
                    filter=[
                        DSLQ("term", visibility=RESTRICTED_VISIBILITY),
                        DSLQ("terms", access_group_ids=sorted(set(viewer_group_ids))),
                    ],
                ),
            ],
            minimum_should_match=1,
        )
    else:
        access = public

    locales = list(dict.fromkeys(locales))
    locale_filter = (
        DSLQ("term", locale=locales[0]) if len(locales) == 1 else DSLQ("terms", locale=locales)
    )
    filters = [
        DSLQ("term", kind=CHUNK_KIND),
        DSLQ("term", content_type=KB_SOURCE),
        locale_filter,
        DSLQ("prefix", family_id=f"{KB_SOURCE}:"),
        access,
    ]
    if product_id is not None:
        filters.append(DSLQ("term", product_ids=str(product_id)))
    return filters


def _aaq_clause(
    parsed: BaseToken,
    *,
    locale: str,
    product_id: int | None,
    default_operator: DefaultOperator,
    minimum_should_match: str | None,
) -> Query:
    search = QuestionSearch(locale=locale)
    lexical_query = _render(
        parsed,
        fields=search.get_fields(),
        settings=search.get_settings(),
        default_operator=default_operator,
        minimum_should_match=minimum_should_match,
    )
    return DSLQ(
        "bool",
        _name=f"lexical:{AAQ_SOURCE}:{locale}",
        filter=[
            DSLQ("term", locale=locale),
            DSLQ("prefix", family_id=f"{AAQ_SOURCE}:"),
        ],
        must=build_question_search_query(
            locale=locale,
            lexical_query=lexical_query,
            product_id=product_id,
            exclude_archived=search.is_simple_search(parsed),
        ),
    )


def build_lexical_clauses(
    query: str,
    *,
    locale: str,
    sources: Collection[Source],
    viewer_group_ids: Sequence[int],
    product_id: int | None = None,
    privileged: bool = False,
    default_operator: DefaultOperator = "AND",
    minimum_should_match: str | None = None,
) -> LexicalClauses:
    """Parse once and build concrete lexical clauses for the requested sources."""
    source_set = frozenset(sources)
    if not source_set or source_set - _SOURCES:
        raise ValueError("sources must contain 'kb', 'aaq', or both")

    try:
        parsed = Parser(query).parsed
    except ParseException:
        parsed = TermToken(query)

    kb_requested = kb_english = aaq_requested = None
    if KB_SOURCE in source_set:
        kb_requested = _kb_clause(
            parsed,
            locale=locale,
            product_id=product_id,
            viewer_group_ids=viewer_group_ids,
            privileged=privileged,
            default_operator=default_operator,
            minimum_should_match=minimum_should_match,
        )
        if locale != ENGLISH_LOCALE:
            kb_english = _kb_clause(
                parsed,
                locale=ENGLISH_LOCALE,
                product_id=product_id,
                viewer_group_ids=viewer_group_ids,
                privileged=privileged,
                default_operator=default_operator,
                minimum_should_match=minimum_should_match,
            )
    if AAQ_SOURCE in source_set:
        aaq_requested = _aaq_clause(
            parsed,
            locale=locale,
            product_id=product_id,
            default_operator=default_operator,
            minimum_should_match=minimum_should_match,
        )

    return LexicalClauses(
        kb_requested=kb_requested,
        kb_english=kb_english,
        aaq_requested=aaq_requested,
    )


def similarity_floor_for_index(index: str) -> float:
    """Resolve the exact configured floor for one concrete index similarity profile."""
    meta = read_index_meta(index)
    _, fingerprint = similarity_profile_fingerprint(meta)
    floors = settings.RETRIEVAL_KNN_SIMILARITY_FLOORS
    floor = floors.get(fingerprint) if isinstance(floors, Mapping) else None
    if not is_valid_similarity_floor(floor, meta["mapping"]["similarity"]):
        raise SimilarityFloorUnavailable(
            f"no valid RETRIEVAL_KNN_SIMILARITY_FLOORS entry for profile {fingerprint}"
        )
    return float(floor)


def _one_or_many(queries: Sequence[Query]) -> Query:
    if len(queries) == 1:
        return queries[0]
    return DSLQ("bool", should=list(queries), minimum_should_match=1)


def _standard_retriever(query: Query) -> dict:
    return {
        "standard": {
            "query": query.to_dict(),
            "collapse": {"field": "family_id"},
        }
    }


def _build_retriever(
    query: str,
    *,
    kb_index: str | None,
    locale: str,
    sources: Collection[Source],
    viewer_group_ids: Sequence[int],
    product_id: int | None,
    query_vector: Sequence[float] | None,
    similarity_floor: float | None,
    semantic_k: int,
    num_candidates: int,
    rank_window_size: int,
    locale_composition: LocaleComposition,
    privileged: bool = False,
    default_operator: DefaultOperator = "AND",
    minimum_should_match: str | None = None,
) -> dict:
    """Build the private native retriever tree used by serving and evaluation."""
    bounds = {
        "semantic_k": semantic_k,
        "num_candidates": num_candidates,
        "rank_window_size": rank_window_size,
    }
    for name, value in bounds.items():
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if num_candidates < semantic_k:
        raise ValueError("num_candidates must be at least semantic_k")
    if locale_composition not in ("combined", "separate"):
        raise ValueError("locale_composition must be 'combined' or 'separate'")

    clauses = build_lexical_clauses(
        query,
        locale=locale,
        sources=sources,
        viewer_group_ids=viewer_group_ids,
        product_id=product_id,
        privileged=privileged,
        default_operator=default_operator,
        minimum_should_match=minimum_should_match,
    )
    requested = [
        clause for clause in (clauses.kb_requested, clauses.aaq_requested) if clause is not None
    ]
    if locale_composition == "combined":
        lexical = [*requested]
        if clauses.kb_english is not None:
            lexical.append(clauses.kb_english)
        retrievers = [_standard_retriever(_one_or_many(lexical))]
    else:
        retrievers = [_standard_retriever(_one_or_many(requested))]
        if clauses.kb_english is not None:
            retrievers.append(_standard_retriever(clauses.kb_english))

    source_set = frozenset(sources)
    if query_vector is not None and KB_SOURCE in source_set:
        if not kb_index:
            raise ValueError("kb_index is required for semantic KB retrieval")
        if not is_valid_similarity_floor(similarity_floor, SIMILARITY):
            raise SimilarityFloorUnavailable(
                "semantic retrieval requires a cosine similarity floor between -1 and 1"
            )
        locales = [locale] if locale == ENGLISH_LOCALE else [locale, ENGLISH_LOCALE]
        semantic_filter = DSLQ(
            "bool",
            filter=[
                DSLQ("term", _index=kb_index),
                *_kb_filters(
                    locales=locales,
                    product_id=product_id,
                    viewer_group_ids=viewer_group_ids,
                    privileged=privileged,
                ),
            ],
        )
        retrievers.append(
            _standard_retriever(
                DSLQ(
                    "knn",
                    _name=f"semantic:{KB_SOURCE}",
                    field="content_vector",
                    query_vector=list(query_vector),
                    k=semantic_k,
                    num_candidates=num_candidates,
                    similarity=float(similarity_floor),
                    filter=semantic_filter,
                )
            )
        )

    if len(retrievers) == 1:
        return retrievers[0]
    return {
        "rrf": {
            "retrievers": retrievers,
            "rank_window_size": rank_window_size,
            "rank_constant": RRF_RANK_CONSTANT,
        }
    }


def _retrieve_unvalidated(
    query: str,
    *,
    kb_index: str | None,
    locale: str,
    sources: Collection[Source],
    viewer_group_ids: Sequence[int],
    product_id: int | None,
    query_vector: Sequence[float] | None,
    similarity_floor: float | None,
    semantic_k: int,
    num_candidates: int,
    rank_window_size: int,
    locale_composition: LocaleComposition,
    page_size: int,
    offset: int,
    max_offset: int,
    privileged: bool = False,
    default_operator: DefaultOperator = "AND",
    minimum_should_match: str | None = None,
    strict: bool = False,
) -> RetrievalResult[UnvalidatedCandidate]:
    """Execute one bounded search and return evidence that still requires authorization."""
    if not isinstance(page_size, int) or isinstance(page_size, bool) or page_size <= 0:
        raise ValueError("page_size must be a positive integer")
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if not isinstance(max_offset, int) or isinstance(max_offset, bool) or max_offset < 0:
        raise ValueError("max_offset must be a non-negative integer")
    if offset > max_offset:
        raise ValueError("offset exceeds max_offset")
    if offset + page_size + 1 > rank_window_size:
        raise ValueError("the page and has_more probe must fit within rank_window_size")

    source_set = frozenset(sources)
    if KB_SOURCE in source_set and not kb_index:
        raise ValueError("kb_index is required when retrieving KB results")
    indices = []
    if kb_index and KB_SOURCE in source_set:
        indices.append(kb_index)
    if AAQ_SOURCE in source_set:
        indices.append(QuestionDocument.Index.read_alias)  # type: ignore[attr-defined]

    retriever = _build_retriever(
        query,
        kb_index=kb_index,
        locale=locale,
        sources=source_set,
        viewer_group_ids=viewer_group_ids,
        product_id=product_id,
        privileged=privileged,
        query_vector=query_vector,
        similarity_floor=similarity_floor,
        semantic_k=semantic_k,
        num_candidates=num_candidates,
        rank_window_size=rank_window_size,
        locale_composition=locale_composition,
        default_operator=default_operator,
        minimum_should_match=minimum_should_match,
    )

    highlight_fields = {}
    if KB_SOURCE in source_set:
        kb_locales = [locale] if locale == ENGLISH_LOCALE else [locale, ENGLISH_LOCALE]
        for kb_locale in kb_locales:
            for field in ("content_text", "summary"):
                highlight_fields[f"{field}.{kb_locale}"] = {
                    "type": "unified",
                    "fragment_size": SNIPPET_LENGTH,
                    "number_of_fragments": 1,
                }
    if AAQ_SOURCE in source_set:
        for field in ("question_content", "answer_content"):
            highlight_fields[f"{field}.{locale}"] = FVH_HIGHLIGHT_OPTIONS

    response = es_client().search(
        index=indices,
        retriever=retriever,
        from_=offset,
        size=page_size + 1,
        collapse={"field": "family_id"},
        aggregations={"families": {"cardinality": {"field": "family_id"}}},
        source_includes=[
            "kind",
            "content_type",
            "object_id",
            "family_id",
            "locale",
            "position",
            "heading_path",
            "scope",
            "content_text",
            "product_ids",
            "topic_ids",
            "category",
            "question_id",
            "question_title",
            "question_content",
            "answer_content",
            "question_updated",
            "question_has_solution",
            "question_num_votes",
        ],
        highlight={
            "fields": highlight_fields,
            "pre_tags": [f"<{HIGHLIGHT_TAG}>"],
            "post_tags": [f"</{HIGHLIGHT_TAG}>"],
        },
        allow_partial_search_results=not strict,
    )
    raw = getattr(response, "body", response)
    if not isinstance(raw, Mapping):
        raise InvalidRetrievalResponse("Elasticsearch returned a non-object response")
    mode: RetrievalMode = (
        "hybrid" if query_vector is not None and KB_SOURCE in source_set else "lexical"
    )
    return _decode_response(raw, page_size=page_size, offset=offset, mode=mode)


def _decode_response(
    response: Mapping, *, page_size: int, offset: int, mode: RetrievalMode
) -> RetrievalResult[UnvalidatedCandidate]:
    shards = response.get("_shards")
    if not isinstance(shards, Mapping):
        raise InvalidRetrievalResponse("response has no shard status")
    successful = shards.get("successful")
    failed = shards.get("failed")
    if not isinstance(successful, int) or isinstance(successful, bool) or successful < 0:
        raise InvalidRetrievalResponse("response has invalid shard counts")
    if not isinstance(failed, int) or isinstance(failed, bool) or failed < 0:
        raise InvalidRetrievalResponse("response has invalid shard counts")
    if successful == 0:
        raise InvalidRetrievalResponse("no Elasticsearch shard completed successfully")

    timed_out = response.get("timed_out", False)
    took = response.get("took")
    if not isinstance(timed_out, bool):
        raise InvalidRetrievalResponse("response has invalid timeout status")
    if not isinstance(took, int) or isinstance(took, bool) or took < 0:
        raise InvalidRetrievalResponse("response has invalid timing")

    hits_block = response.get("hits")
    if not isinstance(hits_block, Mapping) or not isinstance(hits_block.get("hits"), list):
        raise InvalidRetrievalResponse("response has no hit list")
    hits = hits_block["hits"]

    aggregations = response.get("aggregations")
    families = aggregations.get("families") if isinstance(aggregations, Mapping) else None
    approximate_total = families.get("value") if isinstance(families, Mapping) else None
    if (
        not isinstance(approximate_total, int | float)
        or isinstance(approximate_total, bool)
        or not math.isfinite(approximate_total)
        or approximate_total < 0
        or not float(approximate_total).is_integer()
    ):
        raise InvalidRetrievalResponse("response has no valid approximate family count")

    candidates = []
    rejected = 0
    for rank, hit in enumerate(hits[:page_size], start=1):
        try:
            candidates.append(_decode_hit(hit, rank=offset + rank))
        except InvalidRetrievalResponse:
            rejected += 1
    if rejected:
        emit(
            "retrieval.query.hits_rejected",
            level=logging.WARNING,
            rejected_count=rejected,
            inspected_count=min(len(hits), page_size),
        )
    return RetrievalResult(
        candidates=tuple(candidates),
        approximate_total=int(approximate_total),
        has_more=len(hits) > page_size,
        mode=mode,
        degraded=failed > 0 or timed_out or rejected > 0,
        failed_shards=failed,
        took_ms=took,
    )


def _decode_hit(hit: object, *, rank: int) -> UnvalidatedCandidate:
    if not isinstance(hit, Mapping) or not isinstance(hit.get("_source"), Mapping):
        raise InvalidRetrievalResponse("hit has no source object")
    source = hit["_source"]
    family_id = source.get("family_id")
    score = hit.get("_score")
    if not isinstance(family_id, str) or not family_id:
        raise InvalidRetrievalResponse("hit has no family identity")
    if not isinstance(score, int | float) or isinstance(score, bool) or not math.isfinite(score):
        raise InvalidRetrievalResponse("hit has no finite score")
    provenance = _provenance(hit.get("matched_queries"))

    evidence: RetrievalPassage | LegacyQuestion
    if family_id.startswith(f"{KB_SOURCE}:"):
        evidence = _decode_passage(hit, source, family_id, provenance)
    elif family_id.startswith(f"{AAQ_SOURCE}:"):
        evidence = _decode_question(hit, source, family_id, provenance)
    else:
        raise InvalidRetrievalResponse(f"unsupported family identity {family_id!r}")
    return UnvalidatedCandidate(rank, float(score), family_id, evidence)


def _decode_passage(
    hit: Mapping,
    source: Mapping,
    family_id: str,
    provenance: frozenset[RetrievalProvenance],
) -> RetrievalPassage:
    content_type = source.get("content_type")
    object_id = source.get("object_id")
    locale = source.get("locale")
    position = source.get("position")
    heading_path = source.get("heading_path")
    category = source.get("category")
    if source.get("kind") != CHUNK_KIND or content_type != KB_SOURCE:
        raise InvalidRetrievalResponse("KB evidence is not a chunk")
    if parse_positive_integer_id(family_id.removeprefix(f"{KB_SOURCE}:")) is None:
        raise InvalidRetrievalResponse("KB evidence has an invalid family identity")
    if not isinstance(object_id, str) or parse_positive_integer_id(object_id) is None:
        raise InvalidRetrievalResponse("KB evidence has an invalid object identity")
    if not isinstance(locale, str) or not locale or ":" in locale:
        raise InvalidRetrievalResponse("KB evidence has an invalid locale")
    if not isinstance(position, int) or isinstance(position, bool) or position < 0:
        raise InvalidRetrievalResponse("KB evidence has an invalid position")
    if not isinstance(heading_path, str) or not isinstance(category, str):
        raise InvalidRetrievalResponse("KB evidence has invalid metadata")

    return RetrievalPassage(
        content_type=content_type,
        object_id=object_id,
        family_id=family_id,
        locale=locale,
        position=position,
        heading_path=heading_path,
        scope=_scope(source.get("scope")),
        text=_localized_text(source, "content_text", locale),
        provenance=provenance,
        body_highlight=_highlight(hit, "content_text", locale),
        summary_highlight=_highlight(hit, "summary", locale),
        product_ids=_string_ids(source.get("product_ids"), "product_ids"),
        topic_ids=_string_ids(source.get("topic_ids"), "topic_ids"),
        category=category,
    )


def _decode_question(
    hit: Mapping,
    source: Mapping,
    family_id: str,
    provenance: frozenset[RetrievalProvenance],
) -> LegacyQuestion:
    question_id = source.get("question_id")
    if isinstance(question_id, int) and not isinstance(question_id, bool):
        question_id = str(question_id)
    locale = source.get("locale")
    if (
        not isinstance(question_id, str)
        or parse_positive_integer_id(question_id) is None
        or family_id != f"{AAQ_SOURCE}:{question_id}"
    ):
        raise InvalidRetrievalResponse("AAQ evidence has an invalid identity")
    if not isinstance(locale, str) or not locale or ":" in locale:
        raise InvalidRetrievalResponse("AAQ evidence has an invalid locale")

    updated = source.get("question_updated")
    if isinstance(updated, str):
        try:
            updated = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidRetrievalResponse("AAQ evidence has an invalid update time") from exc
    if not isinstance(updated, datetime) or updated.tzinfo is None or updated.utcoffset() is None:
        raise InvalidRetrievalResponse("AAQ evidence has an invalid update time")

    is_solved = source.get("question_has_solution")
    num_votes = source.get("question_num_votes")
    if not isinstance(is_solved, bool):
        raise InvalidRetrievalResponse("AAQ evidence has an invalid solved state")
    if not isinstance(num_votes, int) or isinstance(num_votes, bool):
        raise InvalidRetrievalResponse("AAQ evidence has an invalid vote count")

    answer_content = source.get("answer_content")
    if answer_content is None:
        num_answers = 0
    else:
        values = answer_content.get(locale) if isinstance(answer_content, Mapping) else None
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise InvalidRetrievalResponse("AAQ evidence has invalid answer content")
        num_answers = len(values)

    return LegacyQuestion(
        question_id=question_id,
        family_id=family_id,
        locale=locale,
        title=_localized_text(source, "question_title", locale),
        content=_localized_text(source, "question_content", locale),
        updated=updated,
        is_solved=is_solved,
        num_answers=num_answers,
        num_votes=num_votes,
        provenance=provenance,
        highlight=_highlight(hit, "question_content", locale)
        or _highlight(hit, "answer_content", locale),
    )


def _provenance(value: object) -> frozenset[RetrievalProvenance]:
    if value is None:
        return frozenset()

    names = value.keys() if isinstance(value, Mapping) else value
    if (
        isinstance(names, str | bytes)
        or not isinstance(names, Collection)
        or any(not isinstance(name, str) for name in names)
    ):
        raise InvalidRetrievalResponse("hit has invalid retrieval provenance")
    result: set[RetrievalProvenance] = set()
    for name in names:
        if name.startswith("lexical:"):
            result.add("lexical")
        elif name.startswith("semantic:"):
            result.add("semantic")
    if not result:
        raise InvalidRetrievalResponse("hit has no retrieval provenance")
    return frozenset(result)


def _localized_text(source: Mapping, field: str, locale: str) -> str:
    values = source.get(field)
    value = values.get(locale) if isinstance(values, Mapping) else None
    if not isinstance(value, str):
        raise InvalidRetrievalResponse(f"evidence has no {field}.{locale} text")
    return value


def _highlight(hit: Mapping, field: str, locale: str) -> HighlightFragment | None:
    highlights = hit.get("highlight")
    if highlights is None:
        return None
    if not isinstance(highlights, Mapping):
        raise InvalidRetrievalResponse("hit has invalid highlights")
    fragments = highlights.get(f"{field}.{locale}")
    if fragments is None:
        return None
    if (
        not isinstance(fragments, list)
        or not fragments
        or any(not isinstance(fragment, str) for fragment in fragments)
    ):
        raise InvalidRetrievalResponse(f"hit has invalid {field}.{locale} highlight")
    return HighlightFragment(field, locale, fragments[0])


def _string_ids(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise InvalidRetrievalResponse(f"evidence has invalid {field}")
    return tuple(value)


def _scope(value: object) -> tuple[frozenset[str], ...]:
    if not isinstance(value, Mapping) or set(value) != {"version", "clauses"}:
        raise InvalidRetrievalResponse("evidence has an invalid scope envelope")
    if value["version"] != SCOPE_ENVELOPE_VERSION or isinstance(value["version"], bool):
        raise InvalidRetrievalResponse("evidence has an unsupported scope version")
    clauses = value["clauses"]
    if not isinstance(clauses, list):
        raise InvalidRetrievalResponse("evidence has invalid scope clauses")
    result = []
    for clause in clauses:
        if (
            not isinstance(clause, list)
            or any(not isinstance(selector, str) or not selector for selector in clause)
            or len(set(clause)) != len(clause)
        ):
            raise InvalidRetrievalResponse("evidence has an invalid scope clause")
        result.append(frozenset(clause))
    return tuple(result)
