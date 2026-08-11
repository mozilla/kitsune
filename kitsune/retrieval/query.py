from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Literal

from elasticsearch.dsl import Q as DSLQ
from elasticsearch.dsl.query import Query
from pyparsing import ParseException

from kitsune.retrieval.index import (
    CHUNK_KIND,
    PUBLIC_VISIBILITY,
    RESTRICTED_VISIBILITY,
)
from kitsune.search.parser import Parser
from kitsune.search.parser.tokens import BaseToken, TermToken
from kitsune.search.search import QuestionSearch, WikiSearch, build_question_search_query

KB_SOURCE = "kb"
AAQ_SOURCE = "aaq"
ENGLISH_LOCALE = "en-US"

Source = Literal["kb", "aaq"]
DefaultOperator = Literal["AND", "OR"]
_SOURCES = frozenset({KB_SOURCE, AAQ_SOURCE})


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

    filters = [
        DSLQ("term", kind=CHUNK_KIND),
        DSLQ("term", content_type=KB_SOURCE),
        DSLQ("term", locale=locale),
        DSLQ("prefix", family_id=f"{KB_SOURCE}:"),
        access,
    ]
    if product_id is not None:
        filters.append(DSLQ("term", product_ids=str(product_id)))
    return DSLQ("bool", filter=filters, must=lexical_query)


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
