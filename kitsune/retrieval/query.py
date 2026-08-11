from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from elasticsearch.dsl import Q as DSLQ
from elasticsearch.dsl.query import Query
from pyparsing import ParseException

from kitsune.retrieval.fingerprints import (
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
from kitsune.search.parser import Parser
from kitsune.search.parser.tokens import BaseToken, TermToken
from kitsune.search.search import QuestionSearch, WikiSearch, build_question_search_query

KB_SOURCE = "kb"
AAQ_SOURCE = "aaq"
ENGLISH_LOCALE = "en-US"

Source = Literal["kb", "aaq"]
DefaultOperator = Literal["AND", "OR"]
LocaleComposition = Literal["combined", "separate"]
_SOURCES = frozenset({KB_SOURCE, AAQ_SOURCE})
RRF_RANK_CONSTANT = 60


class SimilarityFloorUnavailable(ImproperlyConfigured):
    """The selected index has no valid environment-specific semantic floor."""


@dataclass(frozen=True)
class LexicalClauses:
    kb_requested: Query | None
    kb_english: Query | None
    aaq_requested: Query | None


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
        locales=[locale], product_id=product_id, viewer_group_ids=viewer_group_ids
    )
    return DSLQ("bool", filter=filters, must=lexical_query)


def _kb_filters(
    *, locales: Sequence[str], product_id: int | None, viewer_group_ids: Sequence[int]
) -> list[Query]:
    if isinstance(viewer_group_ids, str | bytes) or any(
        not isinstance(group_id, int) or isinstance(group_id, bool) or group_id <= 0
        for group_id in viewer_group_ids
    ):
        raise ValueError("viewer_group_ids must contain only positive integers")

    public = DSLQ("term", visibility=PUBLIC_VISIBILITY)
    if viewer_group_ids:
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
            default_operator=default_operator,
            minimum_should_match=minimum_should_match,
        )
        if locale != ENGLISH_LOCALE:
            kb_english = _kb_clause(
                parsed,
                locale=ENGLISH_LOCALE,
                product_id=product_id,
                viewer_group_ids=viewer_group_ids,
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
                ),
            ],
        )
        retrievers.append(
            _standard_retriever(
                DSLQ(
                    "knn",
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
