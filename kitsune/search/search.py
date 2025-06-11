from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from dataclasses import field as dfield
from typing import Optional

import bleach
from dateutil import parser
from django.utils.text import slugify
from elasticsearch.dsl import Q as DSLQ

from kitsune.products.models import Product
from kitsune.search import HIGHLIGHT_TAG, SNIPPET_LENGTH
from kitsune.search.base import SumoSearch
from kitsune.search.documents import (
    ForumDocument,
    ProfileDocument,
    QuestionDocument,
    WikiDocument,
)
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import CATEGORIES
from kitsune.wiki.parser import wiki_to_html

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
        # `highlight` is of type AttrDict, which is internal to elasticsearch_dsl
        # when converted to a dict, it's like:
        # `{ 'es_field_name' : ['highlight1', 'highlight2'], 'field2': ... }`
        # so here we're getting the first item in the first value in that dict:
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
    product: Optional[Product] = None

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
                    "gte": datetime.now(timezone.utc) - timedelta(days=QUESTION_DAYS_DELTA)
                },
            ),
            # exclude archived questions
            DSLQ("term", question_is_archived=False),
        ]

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
        print("=== QuestionSearch.make_result called ===")
        print(f"Input hit object: {hit}")
        print(f"Hit meta: {hit.meta}")
        print(f"Hit question_id: {getattr(hit, 'question_id', 'N/A')}")
        print(f"Hit question_title: {getattr(hit, 'question_title', 'N/A')}")
        question_content_keys = (
            getattr(hit, "question_content", {}).keys()
            if hasattr(hit, "question_content")
            else "N/A"
        )
        print(f"Hit question_content keys: {question_content_keys}")

        # generate a summary for search:
        summary = first_highlight(hit)
        print(f"First highlight result: {summary}")
        if not summary:
            summary = hit.question_content[self.locale][:SNIPPET_LENGTH]
            print(f"Using question_content summary: {summary[:100]}...")
        summary = strip_html(summary)
        print(f"Summary after HTML stripping: {summary[:100]}...")

        # for questions that have no answers, set to None:
        answer_content = getattr(hit, "answer_content", None)
        print(f"Answer content: {answer_content}")

        result = {
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
        print(f"Final QuestionSearch result: {result}")
        print("=== QuestionSearch.make_result completed ===\n")
        return result


@dataclass
class WikiSearch(SumoSearch):
    """Search over Knowledge Base articles."""

    locale: str = "en-US"
    product: Optional[Product] = None

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
        print("=== WikiSearch.make_result called ===")
        print(f"Input hit object: {hit}")
        print(f"Hit meta: {hit.meta}")
        print(f"Hit slug: {getattr(hit, 'slug', 'N/A')}")
        print(f"Hit title: {getattr(hit, 'title', 'N/A')}")
        print(f"Hit summary: {getattr(hit, 'summary', 'N/A')}")
        content_keys = getattr(hit, "content", {}).keys() if hasattr(hit, "content") else "N/A"
        print(f"Hit content keys: {content_keys}")

        # generate a summary for search:
        summary = first_highlight(hit)
        print(f"First highlight result: {summary}")
        if not summary and hasattr(hit, "summary"):
            summary = getattr(hit.summary, self.locale, None)
            print(f"Using hit.summary for locale {self.locale}: {summary}")
        if not summary:
            summary = hit.content[self.locale][:SNIPPET_LENGTH]
            print(f"Using content summary: {summary[:100]}...")
        summary = strip_html(summary)
        print(f"Summary after HTML stripping: {summary[:100]}...")

        result = {
            "type": "document",
            "url": reverse("wiki.document", args=[hit.slug[self.locale]], locale=self.locale),
            "score": hit.meta.score,
            "title": hit.title[self.locale],
            "search_summary": summary,
        }
        print(f"Final WikiSearch result: {result}")
        print("=== WikiSearch.make_result completed ===\n")
        return result


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
        print("=== ProfileSearch.make_result called ===")
        print(f"Input hit object: {hit}")
        print(f"Hit meta: {hit.meta}")
        print(f"Hit username: {getattr(hit, 'username', 'N/A')}")
        print(f"Hit name: {getattr(hit, 'name', 'N/A')}")
        print(f"Hit avatar: {getattr(hit, 'avatar', 'N/A')}")
        print(f"Hit meta.id: {getattr(hit.meta, 'id', 'N/A')}")

        result = {
            "type": "user",
            "avatar": getattr(hit, "avatar", None),
            "username": hit.username,
            "name": getattr(hit, "name", ""),
            "user_id": hit.meta.id,
        }
        print(f"Final ProfileSearch result: {result}")
        print("=== ProfileSearch.make_result completed ===\n")
        return result


@dataclass
class ForumSearch(SumoSearch):
    """Search over User Profiles."""

    thread_forum_id: Optional[int] = None

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
        print("=== ForumSearch.make_result called ===")
        print(f"Input hit object: {hit}")
        print(f"Hit meta: {hit.meta}")
        print(f"Hit thread_title: {getattr(hit, 'thread_title', 'N/A')}")
        hit_content = getattr(hit, "content", "N/A")[:100] if hasattr(hit, "content") else "N/A"
        print(f"Hit content: {hit_content}...")
        print(f"Hit updated: {getattr(hit, 'updated', 'N/A')}")
        print(f"Hit forum_slug: {getattr(hit, 'forum_slug', 'N/A')}")
        print(f"Hit thread_id: {getattr(hit, 'thread_id', 'N/A')}")

        # Process content for summary
        raw_content = hit.content
        print(f"Raw content: {raw_content[:100]}...")
        html_content = wiki_to_html(raw_content)
        print(f"HTML content after wiki_to_html: {html_content[:100]}...")
        stripped_content = strip_html(html_content)
        print(f"Stripped content: {stripped_content[:100]}...")
        final_summary = stripped_content[:1000]
        print(f"Final summary (first 1000 chars): {final_summary[:100]}...")

        # Parse updated date
        parsed_date = parser.parse(hit.updated)
        print(f"Parsed updated date: {parsed_date}")

        result = {
            "type": "thread",
            "title": hit.thread_title,
            "search_summary": final_summary,
            "last_updated": parsed_date,
            "url": reverse(
                "forums.posts",
                kwargs={"forum_slug": hit.forum_slug, "thread_id": hit.thread_id},
            )
            + f"#post-{hit.meta.id}",
        }
        print(f"Final ForumSearch result: {result}")
        print("=== ForumSearch.make_result completed ===\n")
        return result


@dataclass
class CompoundSearch(SumoSearch):
    """Combine a number of SumoSearch classes into one search."""

    _children: list[SumoSearch] = dfield(default_factory=list, init=False)
    _parse_query: bool = True

    @property  # type: ignore
    def parse_query(self):
        return self._parse_query

    @parse_query.setter
    def parse_query(self, value):
        """Set value of parse_query across all children."""
        self._parse_query = value
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
                # if the attribute's value is itself a list, unpack it
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
        # `should` with `minimum_should_match=1` acts like an OR filter
        return DSLQ("bool", should=self._from_children("get_filter"), minimum_should_match=1)

    def make_result(self, hit):
        print("=== CompoundSearch.make_result called ===")
        print(f"Input hit object: {hit}")
        print(f"Hit meta: {hit.meta}")
        print(f"Hit meta.index: {getattr(hit.meta, 'index', 'N/A')}")
        print(f"Number of children: {len(self._children)}")

        index = hit.meta.index
        print(f"Looking for child that matches index: {index}")

        for i, child in enumerate(self._children):
            child_index = child.get_index()
            print(f"Child {i}: {type(child).__name__}, index: {child_index}")
            if same_base_index(index, child_index):
                print(f"Found matching child {i}: {type(child).__name__}")
                result = child.make_result(hit)
                child_name = type(child).__name__
                print(f"Final CompoundSearch result (delegated to {child_name}): {result}")
                print("=== CompoundSearch.make_result completed ===\n")
                return result

        print(f"ERROR: No matching child found for index {index}")
        print("=== CompoundSearch.make_result completed with ERROR ===\n")
        return None
