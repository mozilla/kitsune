from datetime import datetime, timezone, timedelta

import bleach
from elasticsearch_dsl import Q as DSLQ

from kitsune.search import HIGHLIGHT_TAG, SNIPPET_LENGTH
from kitsune.search.config import QUESTION_INDEX_NAME, WIKI_DOCUMENT_INDEX_NAME
from kitsune.search.v2.base import SumoSearch
from kitsune.sumo.urlresolvers import reverse

QUESTION_DAYS_DELTA = 365 * 2


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


class QuestionSearch(SumoSearch):
    """Search over questions."""

    def __init__(self, locale="en-US", product=None, **kwargs):
        self.locale = locale
        self.product = product
        super().__init__(**kwargs)

    def get_index(self):
        return QUESTION_INDEX_NAME

    def get_fields(self):
        return [
            # ^x boosts the score from that field by x amount
            f"question_title.{self.locale}^4",
            f"question_content.{self.locale}^3",
            f"answer_content.{self.locale}^3",
        ]

    def get_highlight_fields(self):
        return [
            f"question_content.{self.locale}",
            f"answer_content.{self.locale}",
        ]

    def get_filter(self):
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
        return WIKI_DOCUMENT_INDEX_NAME

    def get_fields(self):
        return [
            # ^x boosts the score from that field by x amount
            f"keywords.{self.locale}^8",
            f"title.{self.locale}^6",
            f"summary.{self.locale}^2",
            f"content.{self.locale}^1",
        ]

    def get_highlight_fields(self):
        return [
            f"summary.{self.locale}",
            f"content.{self.locale}",
        ]

    def get_filter(self):
        # Add default filters:
        filters = [
            # limit scope to the Wiki index
            DSLQ("term", _index=self.get_index()),
        ]
        if self.product:
            filters.append(DSLQ("term", product_ids=self.product.id))
        return DSLQ("bool", filter=filters)

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


class CompoundSearch(SumoSearch):
    """Combine a number of SumoSearch classes into one search."""

    def __init__(self, **kwargs):
        self._children = []
        self._kwargs = kwargs
        super().__init__(**kwargs)

    def add(self, child):
        """Add a SumoSearch to search over. Chainable."""
        self._children.append(child(**self._kwargs))
        return self

    def _from_children(self, name, *args, **kwargs):
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

    def get_highlight_fields(self):
        return self._from_children("get_highlight_fields")

    def get_filter(self):
        # `should` with `minimum_should_match=1` acts like an OR filter
        return DSLQ("bool", should=self._from_children("get_filter"), minimum_should_match=1)

    def make_result(self, hit):
        index = hit.meta.index
        for child in self._children:
            if index == child.get_index():
                return child.make_result(hit)
