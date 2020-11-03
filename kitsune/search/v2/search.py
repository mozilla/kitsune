import bleach
from datetime import datetime
from abc import ABC, abstractmethod

from elasticsearch_dsl import Search as DSLSearch, Q
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.config import WIKI_DOCUMENT_INDEX_NAME, QUESTION_INDEX_NAME

HIGHLIGHT_TAG = "strong"


def first_highlight(hit):
    highlight = getattr(hit.meta, "highlight", None)
    if highlight:
        return bleach.clean(
            # `highlight` is of type AttrDict, which is internal to elasticsearch_dsl
            # when converted to a dict, it's like:
            # `{ 'es_field_name' : ['highlight1', 'highlight2'], 'field2': ... }`
            # so here we're getting the first item in the first value in that dict:
            next(iter(highlight.to_dict().values()))[0],
            tags=[HIGHLIGHT_TAG],
            strip=True,
        )
    return None


def sanitize(summary):
    return bleach.clean(
        summary,
        tags=[HIGHLIGHT_TAG],
        strip=True,
    )


class BaseConfig(ABC):
    """Semi-abstract base class for Search configs."""

    @property
    @abstractmethod
    def index(self):
        pass

    @property
    @abstractmethod
    def fields(self):
        """An array of fields to search over."""
        pass

    @property
    @abstractmethod
    def highlight_fields(self):
        """An array of fields to highlight."""
        pass

    @property
    def filter(self):
        """A filter which returns all documents of this type to search over."""
        return Q("match", _index=self.index)

    @abstractmethod
    def product_filter(self, product):
        """A filter which returns documents with the correct product."""
        pass

    @abstractmethod
    def make_result(self, hit, locale):
        """Transform a hit into a result dictionary."""
        pass


class AAQConfig(BaseConfig):
    """Search config for AAQ."""

    index = QUESTION_INDEX_NAME
    fields = [
        "question_title.{}^4",
        "question_content.{}^3",
        "answer_content.{}^3",
    ]
    highlight_fields = ["question_content.{}", "answer_content.{}"]
    # exclude AnswerDocuments from the search:
    filter = Q("bool", must_not=Q("exists", field="updated"))

    def product_filter(self, product):
        return Q("match", question_product_id=product.id)

    def make_result(self, hit, locale):
        locale = hit.locale

        summary = first_highlight(hit)
        if not summary:
            summary = hit.question_content[locale][:500]
        summary = sanitize(summary)

        num_answers = 0
        answer_content = getattr(hit, "answer_content", None)
        if answer_content:
            num_answers = len(answer_content[locale])

        return {
            "type": "question",
            "url": "/questions/{}".format(hit.question_id),
            "score": hit.meta.score,
            "title": hit.question_title[locale],
            "search_summary": summary,
            "last_updated": datetime.fromisoformat(hit.question_updated),
            "is_solved": hit.question_has_solution,
            "num_answers": num_answers,
            "num_votes": hit.question_num_votes,
        }


class KBConfig(BaseConfig):
    """Search config for the Knowledge Base."""

    index = WIKI_DOCUMENT_INDEX_NAME
    fields = [
        "keywords.{}^8",
        "title.{}^6",
        "summary.{}^2",
        "content.{}^1",
    ]
    highlight_fields = ["summary.{}", "content.{}"]

    def product_filter(self, product):
        return Q("match", product_ids=product.id)

    def make_result(self, hit, locale):
        summary = first_highlight(hit)
        if not summary:
            summary = hit.summary[locale]
        if not summary:
            summary = hit.content[locale][:500]
        summary = sanitize(summary)

        return {
            "type": "document",
            "url": "/{}/kb/{}".format(locale, hit.slug[locale]),
            "score": hit.meta.score,
            "title": hit.title[locale],
            "search_summary": summary,
        }


class Search:
    """Create an ES7 Search."""

    def __init__(self, query, language, product=None, page=1):
        self.config_classes = []
        self.query = query
        self.language = language
        self.product = product
        self.page = page

    def add_config(self, config):
        self.config_classes.append(config())

    def execute(self):
        # determine indices to search over, and create DSL search object
        index = ",".join(self._getattr("index"))
        search = DSLSearch(using=es7_client(), index=index)

        # add filters
        filters = self._getattr("filter")
        search = search.query("bool", should=filters)

        # add product filters
        if self.product:
            product_filters = self._getattr("product_filter", self.product)
            search = search.query("bool", should=product_filters)

        # add query
        fields = self._localize_fields(self._getattr("fields"))
        search = search.query(
            "simple_query_string", query=self.query, default_operator="AND", fields=fields
        )

        # add highlights
        highlight_fields = self._localize_fields(self._getattr("highlight_fields"))
        search = search.highlight(
            *highlight_fields,
            type="fvh",
            order="score",
            number_of_fragments=1,
            boundary_scanner="sentence",
            pre_tags=["<{}>".format(HIGHLIGHT_TAG)],
            post_tags=["</{}>".format(HIGHLIGHT_TAG)],
        )

        # do pagination
        start = (self.page - 1) * 10
        search = search[start : start + 10]

        # perform search
        self.hits = search.execute().hits

        self.total = self.hits.total.value if self.hits else 0
        self.results = [self._make_result(hit) for hit in self.hits]

    def _make_result(self, hit):
        index = hit.meta.index
        for config in self.config_classes:
            if index == config.index:
                return config.make_result(hit, self.language)

    def _getattr(self, name, *args, **kwargs):
        """
        Get an attribute from all config_classes.

        Calls callable attributes and flattens lists.
        """
        value = []
        for config in self.config_classes:
            attr = getattr(config, name)
            if callable(attr):
                attr = attr(*args, **kwargs)
            if isinstance(attr, list):
                value = [*value, *attr]
            else:
                value.append(attr)
        return value

    def _localize_fields(self, fields):
        return [field.format(self.language) for field in fields]
