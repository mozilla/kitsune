import logging
from dataclasses import dataclass
from dataclasses import field as dfield
from datetime import UTC, datetime, timedelta
from typing import Self

import bleach
from dateutil import parser
from django.conf import settings
from django.utils.text import slugify
from elasticsearch import RequestError
from elasticsearch.dsl import Q as DSLQ
from elasticsearch.dsl import Search as DSLSearch
from elasticsearch.dsl.query import Query
from pyparsing import ParseException

from kitsune.products.models import Product
from kitsune.search import HIGHLIGHT_TAG, SNIPPET_LENGTH
from kitsune.search.base import SumoSearch
from kitsune.search.documents import (
    ForumDocument,
    ProfileDocument,
    QuestionDocument,
    WikiDocument,
)
from kitsune.search.es_utils import es_client
from kitsune.search.parser import Parser
from kitsune.search.parser.operators import (
    AndOperator,
    FieldOperator,
    NotOperator,
    OrOperator,
    SpaceOperator,
)
from kitsune.search.parser.tokens import ExactToken, RangeToken, TermToken
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import CATEGORIES
from kitsune.wiki.parser import wiki_to_html

log = logging.getLogger("k.search")

QUESTION_DAYS_DELTA = 365 * 2
FVH_HIGHLIGHT_OPTIONS = {
    "type": "fvh",
    # order highlighted fragments by their relevance:
    "order": "score",
    # only get one fragment per field:
    "number_of_fragments": 1,
    # split fragments at the end of sentences:
    "boundary_scanner": "sentence",
    # return fragments roughly this size:
    "fragment_size": SNIPPET_LENGTH,
    # add these tags before/after the highlighted sections:
    "pre_tags": [f"<{HIGHLIGHT_TAG}>"],
    "post_tags": [f"</{HIGHLIGHT_TAG}>"],
}
CATEGORY_EXACT_MAPPING = {
    "dict": {
        # `name` is lazy, using str() to force evaluation:
        slugify(str(name)): _id
        for _id, name in CATEGORIES
    },
    "field": "category",
}


def first_highlight(hit):
    highlight = getattr(hit.meta, "highlight", None)
    if highlight:
        # 'highlight' is of type AttrDict, which is internal to elasticsearch.dsl
        # when converted to a dict, it's like:
        # `{ 'es_field_name' : ['hightlight1', 'highlight2'], 'field2': ... }`
        # so here we're getting the first field item in the first value in that dict:
        return next(iter(highlight.to_dict().values()))[0]
    return None


def strip_html(summary):
    return bleach.clean(
        summary,
        tags=[HIGHLIGHT_TAG],
        strip=True,
    )


def same_base_index(a, b):
    """Check if the base parts of two index names are the same."""
    return a.split("_")[:-1] == b.split("_")[:-1]


@dataclass
class QuestionSearch(SumoSearch):
    """Search over questions."""
    locale: str = "en-US"
    product: Product | None = None

    def get_index(self):
        return QuestionDocument.Index.read_alias

    def get_fields(self):
        return [
            # ^x boosts the score from that field by x amount
            f"question_title.{self.locale}^2",
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
        ]

    def get_settings(self):
        return {
            "field_mappings": {
                "title": f"question_title.{self.locale}",
                "content": [f"question_content.{self.locale}", f"answer_content.{self.locale}"],
                "question": f"question_content.{self.locale}",
                "answer": f"answer_content.{self.locale}",
            },
            "range_allowed": [
                "question_created",
                "question_updated",
                "question_taken_until",
                "question_num_votes",
            ],
        }

    def is_simple_search(self, token=None):
        """Determine if the search query is simple (no advanced operators) or advanced.
        Advanced searches are those containing:
        - Field operators (field:value)
        - Boolean operators (AND, OR, NOT)
        - Range operators (range:field:operator:value)
        - Exact matching (exact:field:value)
        - Quoted phrases ("exact phrase")

        Simple searches contain only basic terms and space-separated phrases.
        """
        if token is None:
            if not self.query or not self.query.strip():
                return True
            try:
                parsed = Parser(self.query)
                return self.is_simple_search(parsed.parsed)
            except ParseException:
                # If parsing fails, it's definitely a simple search
                return True

        # Advanced operators and tokens indicate an advanced search
        if isinstance(
            token, FieldOperator | AndOperator | OrOperator | NotOperator | RangeToken | ExactToken
        ):
            return False

        # TermToken is always simple
        if isinstance(token, TermToken):
            return True

        # SpaceOperator is simple only if all its arguments are simple
        if isinstance(token, SpaceOperator):
            return all(self.is_simple_search(arg) for arg in token.arguments)

        # Any other token types are advanced by default
        return False

    def get_highlight_fields_options(self):
        fields = [
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
        ]
        return [(field, FVH_HIGHLIGHT_OPTIONS) for field in fields]

    def get_filter(self):
        filters = [
            # restrict to the question index
            DSLQ("term", _index=self.get_index()),
            # ensure that there is a title for the passed locale
            DSLQ("exists", field=f"question_title.{self.locale}"),
            # only return questions created within QUESTION_DAYS_DELTA
            DSLQ(
                "range",
                question_created={
                    "gte": datetime.now(UTC) - timedelta(days=QUESTION_DAYS_DELTA)
                },
            ),
        ]

        if self.is_simple_search():
            filters.append(DSLQ("term", question_is_archived=False))

        if self.product:
            filters.append(DSLQ("term", question_product_id=self.product.id))
        return DSLQ(
            "bool",
            filter=filters,
            # exclude AnswerDocuments from the search:
            must_not=DSLQ("exists", field="updated"),
            must=self.build_query(),
        )

    def make_result(self, hit):
        # generate a summary for search:
        summary = first_highlight(hit)
        if not summary:
            summary = hit.question_content[self.locale][:SNIPPET_LENGTH]
        summary = strip_html(summary)

        answer_content = getattr(hit, "answer_content", None)

        return {
            "type": "question",
            "url": reverse("questions.details", kwargs={"question_id": hit.question_id}),
            "score": hit.meta.score,
            "title": hit.question_title[self.locale],
            "search_summary": summary,
            "last_updated": datetime.fromisoformat(hit.question_updated),
            "is_solved": hit.question_has_solution,
            "num_answers": len(answer_content[self.locale]) if answer_content else 0,
            "num_votes": hit.question_num_votes,
        }


@dataclass
class WikiSearch(SumoSearch):
    """Search over Knowledge Base articles."""
    locale: str = "en-US"
    product: Product | None = None

    def get_index(self):
        return WikiDocument.Index.read_alias

    def get_fields(self):
        return [
            # ^x boosts the score from that field by x amount
            f"keywords.{self.locale}^8",
            f"title.{self.locale}^6",
            f"summary.{self.locale}^4",
            f"content.{self.locale}^2",
        ]

    def get_settings(self):
        return {
            "field_mappings": {
                "title": f"title.{self.locale}",
                "content": f"content.{self.locale}",
            },
            "exact_mappings": {
                "category": CATEGORY_EXACT_MAPPING,
            },
            "range_allowed": [
                "updated",
            ],
        }

    def get_highlight_fields_options(self):
        fields = [
            f"summary.{self.locale}",
            f"content.{self.locale}",
        ]
        return [(field, FVH_HIGHLIGHT_OPTIONS) for field in fields]

    def get_filter(self):
        # Add default filters:
        filters = [
            # limit scope to the Wiki index
            DSLQ("term", _index=self.get_index()),
            DSLQ("exists", field=f"title.{self.locale}"),
        ]
        if self.product:
            filters.append(DSLQ("term", product_ids=self.product.id))
        return DSLQ("bool", filter=filters, must=self.build_query())

    def make_result(self, hit):
        # generate a summary for search:
        summary = first_highlight(hit)
        if not summary and hasattr(hit, "summary"):
            summary = getattr(hit.summary, self.locale, None)
        if not summary:
            summary = hit.content[self.locale][:SNIPPET_LENGTH]
        summary = strip_html(summary)

        return {
            "type": "document",
            "url": reverse("wiki.document", args=[hit.slug[self.locale]], locale=self.locale),
            "score": hit.meta.score,
            "title": hit.title[self.locale],
            "search_summary": summary,
            "id": hit.meta.id,
        }


@dataclass
class ProfileSearch(SumoSearch):
    """Search over User Profiles."""
    group_ids: list[int] = dfield(default_factory=list)

    def get_index(self):
        return ProfileDocument.Index.read_alias

    def get_fields(self):
        return ["username", "name"]

    def get_highlight_fields_options(self):
        return []

    def get_filter(self):
        if not self.group_ids:
            # When no group filtering is specified, use simple query
            return self.build_query()

        return DSLQ(
            "boosting",
            positive=self.build_query(),
            negative=DSLQ(
                "bool",
                must_not=DSLQ("terms", group_ids=self.group_ids),
            ),
            negative_boost=0.5,
        )

    def make_result(self, hit):
        return {
            "type": "user",
            "avatar": getattr(hit, "avatar", None),
            "username": hit.username,
            "name": getattr(hit, "name", ""),
            "user_id": hit.meta.id,
        }


@dataclass
class ForumSearch(SumoSearch):
    """Search over Forum posts."""
    thread_forum_id: int | None = None

    def get_index(self):
        return ForumDocument.Index.read_alias

    def get_fields(self):
        return ["thread_title", "content"]

    def get_settings(self):
        return {
            "field_mappings": {
                "title": "thread_title",
            },
            "range_allowed": [
                "thread_created",
                "created",
                "updated",
            ],
        }

    def get_highlight_fields_options(self):
        return []

    def get_filter(self):
        # Add default filters:
        filters = [
            # limit scope to the Forum index
            DSLQ("term", _index=self.get_index())
        ]

        if self.thread_forum_id:
            filters.append(DSLQ("term", thread_forum_id=self.thread_forum_id))
        return DSLQ("bool", filter=filters, must=self.build_query())

    def make_result(self, hit):
        return {
            "type": "thread",
            "title": hit.thread_title,
            "search_summary": strip_html(wiki_to_html(hit.content))[:1000],
            "last_updated": parser.parse(hit.updated),
            "url": reverse(
                "forums.posts",
                kwargs={"forum_slug": hit.forum_slug, "thread_id": hit.thread_id},
            )
            + f"#post-{hit.meta.id}",
        }


@dataclass
class SemanticWikiSearch(WikiSearch):
    """Semantic search over Knowledge Base articles using E5 multilingual model."""
    def build_query(self):
        if not self.query:
            return DSLQ("match_all")
        title_query = DSLQ("semantic", field=f"title_semantic.{self.locale}", query=self.query)
        content_query = DSLQ("semantic", field=f"content_semantic.{self.locale}", query=self.query)
        summary_query = DSLQ("semantic", field=f"summary_semantic.{self.locale}", query=self.query)
        return title_query | content_query | summary_query


@dataclass
class SemanticQuestionSearch(QuestionSearch):
    """Semantic search over questions using ES model."""
    def build_query(self):
        if not self.query:
            return DSLQ("match_all")
        title_query = DSLQ("semantic", field=f"question_title_semantic.{self.locale}", query=self.query)
        content_query = DSLQ("semantic", field=f"question_content_semantic.{self.locale}", query=self.query)
        answer_query = DSLQ("semantic", field=f"answer_content_semantic.{self.locale}", query=self.query)
        return title_query | content_query | answer_query


@dataclass
class CompoundSearch(SumoSearch):
    """Combine a number of SumoSearch classes into one search."""
    _children: list[SumoSearch] = dfield(default_factory=list, init=False)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        # When parse_query is set, propagate to children
        if name == 'parse_query' and hasattr(self, '_children'):
            for child in self._children:
                child.parse_query = value

    def add(self, child):
        """Add a SumoSearch instance to search over. Chainable."""
        self._children.append(child)

    def _from_children(self, name):
        """
        Get an attribute from all children.
        Will flatten lists.
        """
        value = []

        for child in self._children:
            attr = getattr(child, name)()
            if isinstance(attr, list):
                value = [*value, *attr]
            else:
                value.append(attr)
        return value

    def get_index(self):
        return ",".join(self._from_children("get_index"))

    def get_fields(self):
        return self._from_children("get_fields")

    def get_highlight_fields_options(self):
        return self._from_children("get_highlight_fields_options")

    def get_filter(self):
        return DSLQ("bool", should=self._from_children("get_filter"), minimum_should_match=1)

    def make_result(self, hit):
        index = hit.meta.index
        for child in self._children:
            if same_base_index(index, child.get_index()):
                return child.make_result(hit)


# Hybrid search implementation - minimal additions only


class RRFQuery(Query):
    """Custom Query wrapper for RRF (Reciprocal Rank Fusion) queries."""
    name = 'rrf'

    def __init__(self, query_dict, **kwargs):
        self._query_dict = query_dict
        super().__init__(**kwargs)

    def to_dict(self):
        return self._query_dict


@dataclass
class HybridSearch(SumoSearch):
    """
    Base class for hybrid search combining semantic and traditional text search using RRF.
    Supports all existing advanced search syntax while adding semantic capabilities.
    """
    locale: str = "en-US"

    def __post_init__(self):
        if self.query and ':' in self.query:
            try:
                Parser(self.query)
            except ParseException:
                pass

    def run(self, key: int | slice | None = None) -> Self:
        """Override run() to handle RRF hybrid search properly at request level."""
        if key is None:
            key = slice(0, settings.SEARCH_RESULTS_PER_PAGE)

        query = self.build_query()
        if isinstance(query, RRFQuery):
            search = DSLSearch(using=es_client(), index=self.get_index()).params(
                **settings.ES_SEARCH_PARAMS
            )

            for highlight_field, options in self.get_highlight_fields_options():
                search = search.highlight(highlight_field, **options)

            search = search[key]

            rrf_dict = query.to_dict()
            filters = self._get_filters_only()

            if filters:
                for retriever in rrf_dict["retriever"]["rrf"]["retrievers"]:
                    if "standard" in retriever and "query" in retriever["standard"]:
                        original_query = retriever["standard"]["query"]
                        retriever["standard"]["query"] = {
                            "bool": {
                                "filter": filters,
                                "must": original_query
                            }
                        }

            search = search.update_from_dict(rrf_dict)
        else:
            return super().run(key)

        try:
            result = search.execute()
        except RequestError as e:
            if self.parse_query:
                self.parse_query = False
                return self.run(key)
            raise e

        self.hits = result.hits
        self.total = result.hits.total
        if hasattr(self.total, 'value'):
            self.total = self.total.value
        elif isinstance(self.total, dict):
            self.total = self.total.get('value', self.total)
        self.results = [self.make_result(hit) for hit in self.hits]
        self.last_key = key

        return self

    def _get_filters_only(self):
        """Get just the filter part without the query - to be overridden by subclasses."""
        return [DSLQ("term", _index=self.get_index())]

    def build_query(self):
        """Build hybrid query using RRF to combine semantic and traditional text search."""
        if not self.query:
            return DSLQ("match_all")

        if ':' in self.query and not self.query.startswith('field:'):
            log.warning(f"Query '{self.query}' contains field syntax, using traditional search")
            return self._build_text_retriever()

        text_retriever = self._build_text_retriever()
        semantic_retriever = self._build_semantic_retriever()

        if semantic_retriever is None:
            return text_retriever

        rrf_query = {
            "retriever": {
                "rrf": {
                    "retrievers": [
                        {"standard": {"query": text_retriever.to_dict()}},
                        {"standard": {"query": semantic_retriever.to_dict()}}
                    ],
                    "rank_window_size": 100,
                    "rank_constant": 20
                }
            }
        }

        return RRFQuery(rrf_query)

    def _build_text_retriever(self):
        raise NotImplementedError

    def _build_semantic_retriever(self):
        raise NotImplementedError


@dataclass
class HybridWikiSearch(HybridSearch, WikiSearch):
    """Hybrid search for wiki documents combining semantic and traditional text search."""
    def _get_filters_only(self):
        filters = [
            DSLQ("term", _index=self.get_index()),
            DSLQ("exists", field=f"title.{self.locale}"),
        ]
        if self.product:
            filters.append(DSLQ("term", product_ids=self.product.id))
        return filters

    def _build_semantic_retriever(self):
        if not self.query:
            return None
        title_query = DSLQ("semantic", field=f"title_semantic.{self.locale}", query=self.query)
        content_query = DSLQ("semantic", field=f"content_semantic.{self.locale}", query=self.query)
        summary_query = DSLQ("semantic", field=f"summary_semantic.{self.locale}", query=self.query)
        return title_query | content_query | summary_query

    def _build_text_retriever(self):
        wiki_search = WikiSearch(query=self.query, locale=self.locale, product=self.product)
        return wiki_search.build_query()


@dataclass
class HybridQuestionSearch(HybridSearch, QuestionSearch):
    """Hybrid search for question documents combining semantic and traditional text search."""
    def _get_filters_only(self):
        filters = [
            DSLQ("term", _index=self.get_index()),
            DSLQ("exists", field=f"question_title.{self.locale}"),
            DSLQ(
                "range",
                question_created={
                    "gte": datetime.now(UTC) - timedelta(days=QUESTION_DAYS_DELTA)
                },
            ),
            DSLQ("bool", must_not=DSLQ("exists", field="updated")),
        ]

        if hasattr(self, 'is_simple_search') and self.is_simple_search():
            filters.append(DSLQ("term", question_is_archived=False))

        if self.product:
            filters.append(DSLQ("term", question_product_id=self.product.id))

        return filters

    def _build_semantic_retriever(self):
        if not self.query:
            return None
        title_query = DSLQ("semantic", field=f"question_title_semantic.{self.locale}", query=self.query)
        content_query = DSLQ("semantic", field=f"question_content_semantic.{self.locale}", query=self.query)
        answer_query = DSLQ("semantic", field=f"answer_content_semantic.{self.locale}", query=self.query)
        return title_query | content_query | answer_query

    def _build_text_retriever(self):
        question_search = QuestionSearch(query=self.query, locale=self.locale, product=self.product)
        return question_search.build_query()


@dataclass
class HybridCompoundSearch(HybridSearch):
    """
    True hybrid compound search using a single RRF query across wiki and question documents.
    Uses Elasticsearch's native RRF to combine semantic and text search across multiple indices.
    """
    product: Product | None = None

    def get_index(self):
        """Search across both wiki and question indices."""
        return f"{WikiDocument.Index.read_alias},{QuestionDocument.Index.read_alias}"

    def get_fields(self):
        """Get all searchable fields from both wiki and question documents."""
        wiki_fields = [
            f"keywords.{self.locale}^8",
            f"title.{self.locale}^6",
            f"summary.{self.locale}^4",
            f"content.{self.locale}^2",
        ]

        question_fields = [
            f"question_title.{self.locale}^2",
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
        ]

        return wiki_fields + question_fields

    def get_filter(self):
        filters = self._get_filters_only()
        if filters:
            return DSLQ("bool", filter=filters, must=self.build_query())
        else:
            return self.build_query()

    def get_highlight_fields_options(self):
        """Combine highlight fields from both wiki and question searches."""
        fields = []
        for field in [f"summary.{self.locale}", f"content.{self.locale}"]:
            fields.append((field, FVH_HIGHLIGHT_OPTIONS))
        for field in [f"question_content.{self.locale}", f"answer_content.{self.locale}"]:
            fields.append((field, FVH_HIGHLIGHT_OPTIONS))
        return fields

    def _get_filters_only(self):
        """Get combined filters for both wiki and question documents."""
        wiki_filters = [
            DSLQ("term", _index=WikiDocument.Index.read_alias),
            DSLQ("exists", field=f"title.{self.locale}"),
        ]
        if self.product:
            wiki_filters.append(DSLQ("term", product_ids=self.product.id))

        question_filters = [
            DSLQ("term", _index=QuestionDocument.Index.read_alias),
            DSLQ("exists", field=f"question_title.{self.locale}"),
            DSLQ(
                "range",
                question_created={
                    "gte": datetime.now(UTC) - timedelta(days=QUESTION_DAYS_DELTA)
                },
            ),
            DSLQ("bool", must_not=DSLQ("exists", field="updated")),
        ]
        if self.product:
            question_filters.append(DSLQ("term", question_product_id=self.product.id))

        return [
            DSLQ("bool", should=[
                DSLQ("bool", filter=wiki_filters),
                DSLQ("bool", filter=question_filters)
            ], minimum_should_match=1)
        ]

    def _build_semantic_retriever(self):
        if not self.query:
            return None

        wiki_title = DSLQ("semantic", field=f"title_semantic.{self.locale}", query=self.query)
        wiki_content = DSLQ("semantic", field=f"content_semantic.{self.locale}", query=self.query)
        wiki_summary = DSLQ("semantic", field=f"summary_semantic.{self.locale}", query=self.query)

        question_title = DSLQ("semantic", field=f"question_title_semantic.{self.locale}", query=self.query)
        question_content = DSLQ("semantic", field=f"question_content_semantic.{self.locale}", query=self.query)
        answer_content = DSLQ("semantic", field=f"answer_content_semantic.{self.locale}", query=self.query)

        return wiki_title | wiki_content | wiki_summary | question_title | question_content | answer_content

    def _build_text_retriever(self):
        all_fields = self.get_fields()
        return DSLQ("multi_match", query=self.query, fields=all_fields)

    def make_result(self, hit):
        """Route result creation to appropriate handler based on index."""
        index = hit.meta.index
        if same_base_index(index, WikiDocument.Index.read_alias):
            return self._make_wiki_result(hit)
        elif same_base_index(index, QuestionDocument.Index.read_alias):
            return self._make_question_result(hit)
        else:
            return {"type": "unknown", "title": "Unknown result"}

    def _make_wiki_result(self, hit):
        """Make result for wiki document."""
        summary = first_highlight(hit)
        if not summary and hasattr(hit, "summary"):
            summary = getattr(hit.summary, self.locale, None)
        if not summary:
            summary = hit.content[self.locale][:SNIPPET_LENGTH]
        summary = strip_html(summary)

        return {
            "type": "document",
            "url": reverse("wiki.document", args=[hit.slug[self.locale]], locale=self.locale),
            "score": hit.meta.score,
            "title": hit.title[self.locale],
            "search_summary": summary,
            "id": hit.meta.id,
        }

    def _make_question_result(self, hit):
        """Make result for question document."""
        summary = first_highlight(hit)
        if not summary:
            summary = hit.question_content[self.locale][:SNIPPET_LENGTH]
        summary = strip_html(summary)

        answer_content = getattr(hit, "answer_content", None)

        return {
            "type": "question",
            "url": reverse("questions.details", kwargs={"question_id": hit.question_id}),
            "score": hit.meta.score,
            "title": hit.question_title[self.locale],
            "search_summary": summary,
            "last_updated": datetime.fromisoformat(hit.question_updated),
            "is_solved": hit.question_has_solution,
            "num_answers": len(answer_content[self.locale]) if answer_content else 0,
            "num_votes": hit.question_num_votes,
        }
