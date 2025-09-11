from dataclasses import dataclass
from dataclasses import field as dfield
from datetime import UTC, datetime, timedelta
from typing import Self

import bleach
from dateutil import parser
from django.utils.text import slugify
from elasticsearch import RequestError
from elasticsearch.dsl import Q as DSLQ
from elasticsearch.dsl import Search as DSLSearch

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
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import CATEGORIES
from kitsune.wiki.parser import wiki_to_html

QUESTION_DAYS_DELTA = 365 * 2


class RRFQuery:
    def __init__(self, query_dict):
        self.query_dict = query_dict

    def to_dict(self):
        return self.query_dict
FVH_HIGHLIGHT_OPTIONS = {
    "type": "fvh",
    "order": "score",
    "number_of_fragments": 1,
    "boundary_scanner": "sentence",
    "fragment_size": SNIPPET_LENGTH,
    "pre_tags": [f"<{HIGHLIGHT_TAG}>"],
    "post_tags": [f"</{HIGHLIGHT_TAG}>"],
}
CATEGORY_EXACT_MAPPING = {
    "dict": {
        slugify(str(name)): _id
        for _id, name in CATEGORIES
    },
    "field": "category",
}


def first_highlight(hit):
    highlight = getattr(hit.meta, "highlight", None)
    if highlight:
        return next(iter(highlight.to_dict().values()))[0]
    return None


def strip_html(summary):
    return bleach.clean(
        summary,
        tags=[HIGHLIGHT_TAG],
        strip=True,
    )


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
            f"question_title.{self.locale}^1",  # Reduced boost to let wiki titles compete better
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

    def get_advanced_query_field_names(self):
        """Return list of field names that can be used in advanced queries."""
        return ["title", "content", "question", "answer"]

    def get_base_filters(self):
        """Get base filters that apply to all query types."""
        filters = [
            DSLQ("term", _index=self.get_index()),
            DSLQ("exists", field=f"question_title.{self.locale}"),
            DSLQ(
                "range",
                question_created={
                    "gte": datetime.now(UTC) - timedelta(days=QUESTION_DAYS_DELTA)
                },
            ),
        ]
        if not self.is_advanced_query():
            filters.append(DSLQ("term", question_is_archived=False))
        if self.product:
            filters.append(DSLQ("term", question_product_id=self.product.id))
        return filters

    def get_semantic_fields(self):
        """Return semantic fields for QuestionSearch."""
        return [
            "question_title_semantic",
            "question_content_semantic",
            "answer_content_semantic",
        ]

    def _apply_filters_to_query(self, query):
        """Apply question-specific filters to a query."""
        return DSLQ(
            "bool",
            filter=self.get_base_filters(),
            must_not=DSLQ("exists", field="updated"),
            must=query
        )

    def build_query(self):
        """Build query - use hybrid RRF for simple queries, traditional for advanced."""
        if self.is_advanced_query():
            # Advanced query - use traditional parser with field operator support
            return self.build_traditional_query_with_filters(strict_matching=True)
        else:
            # Simple query - use hybrid RRF (handles difficult queries better)
            return self.build_hybrid_rrf_query()

    def get_highlight_fields_options(self):
        fields = [
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
        ]
        return [(field, FVH_HIGHLIGHT_OPTIONS) for field in fields]

    def get_filter(self):
        # Check if we're building an RRF query
        query = self.build_query()
        if isinstance(query, RRFQuery):
            # For RRF queries, filters are already applied inside the retrievers
            return query
        else:
            # Traditional query flow
            return DSLQ(
                "bool",
                filter=self.get_base_filters(),
                must_not=DSLQ("exists", field="updated"),
                must=query
            )

    def make_result(self, hit):
        # generate a summary for search:
        summary = first_highlight(hit)
        if not summary:
            summary = hit.question_content[self.locale][:SNIPPET_LENGTH]
        summary = strip_html(summary)

        # for questions that have no answers, set to None:
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
            f"title.{self.locale}^15",  # Further increased boost for wiki titles to beat questions
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

    def get_advanced_query_field_names(self):
        """Return list of field names that can be used in advanced queries."""
        return ["title", "content", "category"]

    def get_base_filters(self):
        """Get base filters that apply to all query types."""
        filters = [
            DSLQ("term", _index=self.get_index()),
            DSLQ("exists", field=f"title.{self.locale}"),
        ]
        if self.product:
            filters.append(DSLQ("term", product_ids=self.product.id))
        return filters

    def get_semantic_fields(self):
        """Return semantic fields for WikiSearch."""
        return [
            "title_semantic",
            "content_semantic",
            "summary_semantic",
        ]

    def build_query(self):
        """Build query - use hybrid RRF for simple queries, traditional for advanced."""
        if self.is_advanced_query():
            # Advanced query - use traditional parser with field operator support
            return self.build_traditional_query_with_filters(strict_matching=True)
        else:
            # Simple query - use hybrid RRF (handles difficult queries better)
            return self.build_hybrid_rrf_query()


    def get_filter(self):
        # Check if we're building an RRF query
        query = self.build_query()
        if isinstance(query, RRFQuery):
            # For RRF queries, filters are already applied inside the retrievers
            return query
        else:
            # Traditional query flow
            return DSLQ("bool", filter=self.get_base_filters(), must=query)

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
    """Search over User Profiles."""

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
class UnifiedRRFSearch(SumoSearch):
    """Unified search using RRF to combine all search types (questions, wiki, etc.)."""

    locale: str = "en-US"
    product: Product | None = None
    group_ids: list[int] = dfield(default_factory=list)
    thread_forum_id: int | None = None
    min_score: float = 0.005  # Lower threshold for RRF scores to return more results

    def __post_init__(self):
        # Cache search instances to avoid repeated creation
        self._question_search = None
        self._wiki_search = None
        self._profile_search = None
        self._forum_search = None

    @property
    def question_search(self):
        if self._question_search is None:
            self._question_search = QuestionSearch(query=self.query, locale=self.locale, product=self.product)
        return self._question_search

    @property
    def wiki_search(self):
        if self._wiki_search is None:
            self._wiki_search = WikiSearch(query=self.query, locale=self.locale, product=self.product)
        return self._wiki_search

    @property
    def profile_search(self):
        if self._profile_search is None:
            self._profile_search = ProfileSearch(query=self.query, group_ids=self.group_ids)
        return self._profile_search

    @property
    def forum_search(self):
        if self._forum_search is None:
            self._forum_search = ForumSearch(query=self.query, thread_forum_id=self.thread_forum_id)
        return self._forum_search

    def build_rrf_query(self):
        """Build a combined query - this is used for advanced queries only."""
        should_queries = []

        # Use cached instances
        should_queries.append(self.question_search.build_query())
        should_queries.append(self.wiki_search.build_query())
        should_queries.append(self.profile_search.build_query())
        should_queries.append(self.forum_search.build_query())

        # Combine with bool query
        combined_query = DSLQ("bool", should=should_queries, minimum_should_match=1)
        return combined_query

    def get_index(self):
        """Return combined index names for all search types - programmatically derived from child searches."""
        indices = [
            self.question_search.get_index(),
            self.wiki_search.get_index(),
            self.profile_search.get_index(),
            self.forum_search.get_index(),
        ]
        return ",".join(indices)

    def get_fields(self):
        return [
            f"question_title.{self.locale}^2",
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
            f"keywords.{self.locale}^8",
            f"title.{self.locale}^6",
            f"summary.{self.locale}^4",
            f"content.{self.locale}^2",
            "username",
            "name",
            "thread_title",
        ]

    def get_highlight_fields_options(self):
        """Return combined highlight fields from all child searches."""
        highlight_fields = []

        # Collect highlight fields from all child searches
        for search in [self.question_search, self.wiki_search, self.profile_search, self.forum_search]:
            highlight_fields.extend(search.get_highlight_fields_options())

        return highlight_fields

    def get_filter(self):
        if self._is_simple_query():
            return self.build_rrf_query()
        else:
            # For advanced queries, return traditional query
            return DSLQ("bool", filter=self.get_base_filters(), must=self.build_query())

    def run(self, key: int | slice = slice(0, 10)) -> Self:
        """Override run to handle RRF queries properly."""
        if self._is_simple_query():
            # Use RRF for simple queries
            return self._run_rrf_search(key)
        else:
            # Use traditional search for advanced queries
            return self._run_traditional_search(key)

    def _is_simple_query(self):
        """Check if query is simple (not advanced) across all search types."""
        return not (self.question_search.is_advanced_query() or self.wiki_search.is_advanced_query())

    def _gather_individual_search_results(self):
        """Execute individual search types and gather results."""
        all_results = []

        # QuestionSearch RRF
        self.question_search.run(slice(0, 50))
        all_results.extend(self.question_search.results)

        # WikiSearch RRF
        self.wiki_search.run(slice(0, 50))
        all_results.extend(self.wiki_search.results)

        # ProfileSearch (traditional)
        self.profile_search.run(slice(0, 100))
        all_results.extend(self.profile_search.results)

        # ForumSearch (traditional)
        self.forum_search.run(slice(0, 100))
        all_results.extend(self.forum_search.results)

        return all_results


    def _apply_pagination(self, all_results, key):
        """Apply pagination to sorted results."""
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop or len(all_results)
            return all_results[start:stop]
        else:
            return all_results[key:key+1]

    def _run_rrf_search(self, key: int | slice) -> Self:
        """Run RRF search by executing individual RRF queries and combining results."""
        all_results = self._gather_individual_search_results()

        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)

        if self.min_score > 0:
            all_results = [r for r in all_results if r.get('score', 0) >= self.min_score]

        paginated_results = self._apply_pagination(all_results, key)

        self.results = paginated_results
        self.total = len(all_results)
        self.hits = []
        self.last_key = key

        return self

    def _run_traditional_search(self, key: int | slice) -> Self:
        """Run traditional search for advanced queries."""
        from django.conf import settings

        # Traditional DSL search flow
        search = DSLSearch(using=es_client(), index=self.get_index()).params(
            **settings.ES_SEARCH_PARAMS
        )

        # Get the filter/query
        filter_or_query = self.get_filter()

        # add the search class' filter
        search = search.query(filter_or_query)

        # Apply min_score if set
        if self.min_score > 0:
            search = search.extra(min_score=self.min_score)

        # add highlights for the search class' highlight_fields
        for highlight_field, options in self.get_highlight_fields_options():
            search = search.highlight(highlight_field, **options)
        # slice search
        search = search[key]

        # perform search
        try:
            result = search.execute()
        except RequestError as e:
            if self.parse_query:
                # try search again, but without parsing any advanced syntax
                self.parse_query = False
                return self.run(key)
            raise e

        self.hits = result.hits
        self.last_key = key
        self.total = self.hits.total.value  # type: ignore
        self.results = [self.make_result(hit) for hit in self.hits]

        return self
    def make_result(self, hit):
        index = hit.meta.index
        if "question" in index:
            return self.question_search.make_result(hit)
        elif "wiki" in index:
            return self.wiki_search.make_result(hit)
        elif "profile" in index:
            return self.profile_search.make_result(hit)
        elif "forum" in index:
            return self.forum_search.make_result(hit)
        else:
            return {}


# Alias for backward compatibility
UnifiedSearch = UnifiedRRFSearch
