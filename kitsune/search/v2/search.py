from datetime import datetime, timedelta, timezone

import bleach
from dateutil import parser
from elasticsearch_dsl import Q as DSLQ

from kitsune.search import HIGHLIGHT_TAG, SNIPPET_LENGTH
from kitsune.search.v2.base import SumoSearch
from kitsune.search.v2.documents import (
    ForumDocument,
    ProfileDocument,
    QuestionDocument,
    WikiDocument,
)
from kitsune.sumo.urlresolvers import reverse
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


class QuestionSearch(SumoSearch):
    """Search over questions."""

    def __init__(self, locale="en-US", product=None, **kwargs):
        self.locale = locale
        self.product = product
        super().__init__(**kwargs)

    def get_index(self):
        return QuestionDocument.Index.read_alias

    def get_fields(self):
        return [
            # ^x boosts the score from that field by x amount
            f"question_title.{self.locale}^2",
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
        ]

    def get_highlight_fields_options(self):
        fields = [
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
        ]
        return [(field, FVH_HIGHLIGHT_OPTIONS) for field in fields]

    def get_filter(self, **kwargs):
        filters = [
            # restrict to the question index
            DSLQ("term", _index=self.get_index()),
            # only return questions created within QUESTION_DAYS_DELTA
            DSLQ(
                "range",
                question_created={
                    "gte": datetime.now(timezone.utc) - timedelta(days=QUESTION_DAYS_DELTA)
                },
            ),
        ]
        if self.product:
            filters.append(DSLQ("term", question_product_id=self.product.id))
        return DSLQ(
            "bool",
            filter=filters,
            # exclude AnswerDocuments from the search:
            must_not=DSLQ("exists", field="updated"),
            must=self.build_query(**kwargs),
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


class WikiSearch(SumoSearch):
    """Search over Knowledge Base articles."""

    def __init__(self, locale="en-US", product=None, **kwargs):
        self.locale = locale
        self.product = product
        super().__init__(**kwargs)

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

    def get_highlight_fields_options(self):
        fields = [
            f"summary.{self.locale}",
            f"content.{self.locale}",
        ]
        return [(field, FVH_HIGHLIGHT_OPTIONS) for field in fields]

    def get_filter(self, **kwargs):
        # Add default filters:
        filters = [
            # limit scope to the Wiki index
            DSLQ("term", _index=self.get_index()),
        ]
        if self.product:
            filters.append(DSLQ("term", product_ids=self.product.id))
        return DSLQ("bool", filter=filters, must=self.build_query(**kwargs))

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
        }


class ProfileSearch(SumoSearch):
    """Search over User Profiles."""

    def get_index(self):
        return ProfileDocument.Index.read_alias

    def get_fields(self):
        return ["username", "name"]

    def get_highlight_fields_options(self):
        return []

    def get_filter(self, **kwargs):
        return DSLQ(
            "boosting",
            positive=self.build_query(**kwargs),
            negative=DSLQ(
                "bool",
                must_not=DSLQ("terms", group_ids=kwargs.get("group_ids", [])),
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


class ForumSearch(SumoSearch):
    """Search over User Profiles."""

    def get_index(self):
        return ForumDocument.Index.read_alias

    def get_fields(self):
        return ["thread_title", "content"]

    def get_highlight_fields_options(self):
        return []

    def get_filter(self, **kwargs):
        # Add default filters:
        filters = [
            # limit scope to the Forum index
            DSLQ("term", _index=self.get_index())
        ]

        if thread_forum_id := kwargs.get("thread_forum_id"):
            filters.append(DSLQ("term", thread_forum_id=thread_forum_id))
        return DSLQ("bool", filter=filters, must=self.build_query(**kwargs))

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


class CompoundSearch(SumoSearch):
    """Combine a number of SumoSearch classes into one search."""

    def __init__(self, **kwargs):
        self._children = []
        self._kwargs = kwargs
        super().__init__(**kwargs)

    def add(self, child):
        """Add a SumoSearch to search over. Chainable."""
        self._children.append(child(**self._kwargs))

    def _from_children(self, name, **kwargs):
        """
        Get an attribute from all children.

        Will flatten lists.
        """
        value = []

        for child in self._children:
            attr = getattr(child, name)(**kwargs)
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

    def get_filter(self, **kwargs):
        # `should` with `minimum_should_match=1` acts like an OR filter
        return DSLQ(
            "bool", should=self._from_children("get_filter", **kwargs), minimum_should_match=1
        )

    def make_result(self, hit):
        index = hit.meta.index
        for child in self._children:
            if same_base_index(index, child.get_index()):
                return child.make_result(hit)
