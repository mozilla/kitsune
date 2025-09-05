from abc import ABC, abstractmethod
from dataclasses import dataclass
from dataclasses import field as dfield
from datetime import datetime
from typing import Self, overload

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.core.paginator import Paginator as DjPaginator
from django.utils import timezone
from django.utils.translation import gettext as _
from elasticsearch import NotFoundError, RequestError
from elasticsearch.dsl import Document as DSLDocument
from elasticsearch.dsl import InnerDoc, MetaField, field
from elasticsearch.dsl import Q as DSLQ
from elasticsearch.dsl import Search as DSLSearch
from elasticsearch.dsl.utils import AttrDict
from pyparsing import ParseException

from kitsune.search.config import (
    DEFAULT_ES_CONNECTION,
    DEFAULT_ES_REFRESH_INTERVAL,
    UPDATE_RETRY_ON_CONFLICT,
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


class SumoDocument(DSLDocument):
    """Base class with common methods for all the different documents."""

    # Controls if a document should be indexed or updated in ES.
    #   True: An update action will be performed in ES.
    #   False: An index action will be performed in ES.
    update_document = False

    indexed_on = field.Date()

    class Meta:
        # ignore fields if they don't exist in the mapping
        dynamic = MetaField("false")

    def __init_subclass__(cls, **kwargs):
        """Automatically set up each subclass' Index attribute."""
        super().__init_subclass__(**kwargs)

        cls.Index.using = DEFAULT_ES_CONNECTION

        # this is here to ensure subclasses of subclasses of SumoDocument (e.g. AnswerDocument)
        # use the same name in their index as their parent class (e.g. QuestionDocument) since
        # they share an index with that parent
        immediate_parent = cls.__mro__[1]
        if immediate_parent is SumoDocument:
            name = cls.__name__
        else:
            name = immediate_parent.__name__

        cls.Index.base_name = f"{settings.ES_INDEX_PREFIX}_{name.lower()}"
        cls.Index.read_alias = f"{cls.Index.base_name}_read"
        cls.Index.write_alias = f"{cls.Index.base_name}_write"
        # Bump the refresh interval to 1 minute
        cls.Index.settings = {"refresh_interval": DEFAULT_ES_REFRESH_INTERVAL}

        # this is the attribute elastic-dsl actually uses to determine which index
        # to query. we override the .search() method to get that to use the read
        # alias:
        cls.Index.name = cls.Index.write_alias

    @classmethod
    def search(cls, **kwargs):
        """
        Create an `elasticsearch_dsl.Search` instance that will search over this `Document`.

        If no `index` kwarg is supplied, use the Document's Index's `read_alias`.
        """
        if "index" not in kwargs:
            kwargs["index"] = cls.Index.read_alias
        return super().search(**kwargs)

    @classmethod
    def migrate_writes(cls, timestamp=None):
        """Create a new index for this document, and point the write alias at it."""
        timestamp = timestamp or datetime.now(tz=timezone.utc)
        name = f"{cls.Index.base_name}_{timestamp.strftime('%Y%m%d%H%M%S')}"
        cls.init(index=name)
        cls._update_alias(cls.Index.write_alias, name)

    @classmethod
    def migrate_reads(cls):
        """Point the read alias at the same index as the write alias."""
        cls._update_alias(cls.Index.read_alias, cls.alias_points_at(cls.Index.write_alias))

    @classmethod
    def _update_alias(cls, alias, new_index):
        client = es_client()
        old_index = cls.alias_points_at(alias)
        if not old_index:
            client.indices.put_alias(index=new_index, name=alias)
        else:
            client.indices.update_aliases(
                actions=[
                    {"remove": {"index": old_index, "alias": alias}},
                    {"add": {"index": new_index, "alias": alias}},
                ]
            )

    @classmethod
    def alias_points_at(cls, alias):
        """Returns the index `alias` points at."""
        try:
            aliased_indices = list(es_client().indices.get_alias(name=alias))
        except NotFoundError:
            aliased_indices = []

        if len(aliased_indices) > 1:
            raise RuntimeError(
                f"{alias} points at more than one index, something has gone very wrong"
            )

        return aliased_indices[0] if aliased_indices else None

    @classmethod
    def prepare(cls, instance, parent_id=None, **kwargs):
        """Prepare an object given a model instance.

        parent_id: Supplying a parent_id will ignore any fields which aren't a
        SumoLocaleAware field, and set the meta.id value to the parent_id one.
        """

        obj = cls()

        doc_mapping = obj._doc_type.mapping
        fields = list(doc_mapping)
        fields.remove("indexed_on")
        # Loop through the fields of each object and set the right values

        # check if the instance is suitable for indexing
        # the prepare method of each Document Type can mark an object
        # not suitable for indexing based on criteria defined on each said method
        if not hasattr(instance, "es_discard_doc"):
            for f in fields:
                # This will allow child classes to have their own methods
                # in the form of prepare_field
                prepare_method = getattr(obj, f"prepare_{f}", None)
                value = obj.get_field_value(f, instance, prepare_method)

                # Assign values to each field.
                field_type = doc_mapping.resolve_field(f)
                if isinstance(field_type, field.Object) and not (
                    isinstance(value, InnerDoc)
                    or (isinstance(value, list) and isinstance((value or [None])[0], InnerDoc))
                ):
                    # if the field is an Object but the value isn't an InnerDoc
                    # or a list containing an InnerDoc then we're dealing with locales
                    locale = obj.prepare_locale(instance)
                    # Check specifically against None, False is a valid value
                    if locale and (value is not None):
                        obj[f] = {locale: value}

                else:
                    if (
                        isinstance(field_type, field.Date)
                        and isinstance(value, datetime)
                        and timezone.is_naive(value)
                    ):
                        value = timezone.make_aware(value).astimezone(timezone.utc)

                    if not parent_id:
                        setattr(obj, f, value)
        else:
            obj.es_discard_doc = "unindex_me"

        obj.indexed_on = datetime.now(timezone.utc)
        obj.meta.id = instance.pk
        if parent_id:
            obj.meta.id = parent_id

        return obj

    def to_action(self, action=None, is_bulk=False, **kwargs):
        """Method to construct the data for save, delete, update operations.

        Useful for bulk operations.
        """

        # If an object has a discard field then mark it for deletion if exists
        # This is the only case where this method ignores the passed arg action and
        # overrides it with a deletion. This can happen if the `prepare` method of each
        # document type has marked a document as not suitable for indexing
        if hasattr(self, "es_discard_doc"):
            # Let's try to delete anything that might exist in ES
            action = "delete"
            kwargs = {}

        # Default to index if no action is defined or if it's `save`
        # if we have a bulk update, we need to include the meta info
        # and return the data by calling the to_dict() method of DSL
        payload = self.to_dict(include_meta=is_bulk, skip_empty=False)

        # If we are in a test environment, mark refresh=True so that
        # documents will be updated/added directly in the index.
        if settings.TEST and not is_bulk:
            kwargs.update({"refresh": True})

        if not action or action == "index":
            return payload if is_bulk else self.save(**kwargs)
        elif action == "update":
            # add any additional args like doc_as_upsert
            payload.update(kwargs)

            if is_bulk:
                # this is a bit idiomatic b/c dsl does not have a wrapper around bulk operations
                # we need to return the payload and let elasticsearch-py bulk method deal with
                # the update
                payload["doc"] = payload["_source"]
                payload.update(
                    {
                        "_op_type": "update",
                        "retry_on_conflict": UPDATE_RETRY_ON_CONFLICT,
                    }
                )
                del payload["_source"]
                return payload
            return self.update(**payload)
        elif action == "delete":
            # if we have a bulk operation, drop the _source and mark the operation as deletion
            if is_bulk:
                payload.update({"_op_type": "delete"})
                del payload["_source"]
                return payload
            # This is a single document op, delete it
            kwargs.update({"ignore": [400, 404]})
            return self.delete(**kwargs)

    @classmethod
    def get_queryset(cls):
        """
        Return the manager for a document's model.
        This allows child classes to add optimizations like select_related or prefetch_related
        to improve indexing performance.
        """
        return cls.get_model()._default_manager

    def get_field_value(self, field, instance, prepare_method):
        """Allow child classes to define their own logic for getting field values."""
        if prepare_method is not None:
            return prepare_method(instance)
        return getattr(instance, field)

    def prepare_locale(self, instance):
        """Return the locale of an object if exists."""
        if instance.locale:
            return instance.locale
        return ""


class SumoSearchInterface(ABC):
    """Base interface class for search classes.

    Child classes should define values for the various abstract properties this
    class has, relevant to the documents the child class is searching over.
    """

    @abstractmethod
    def get_index(self):
        """The index or comma-seperated indices to search over."""
        ...

    @abstractmethod
    def get_fields(self):
        """An array of fields to search over."""
        ...

    def get_settings(self):
        """Configuration for advanced search."""
        ...

    @abstractmethod
    def get_highlight_fields_options(self):
        """An array of tuples of fields to highlight and their options."""
        ...

    @abstractmethod
    def get_filter(self):
        """A query which filters for all documents to be searched over."""
        ...

    @abstractmethod
    def build_query(self):
        """Build a query to search over a specific set of documents."""
        ...

    @abstractmethod
    def make_result(self, hit):
        """Takes a hit and returns a result dictionary."""
        ...

    @abstractmethod
    def run(self, *args, **kwargs) -> Self:
        """Perform search, placing the results in `self.results`, and the total
        number of results (across all pages) in `self.total`. Chainable."""
        ...


@dataclass
class SumoSearch(SumoSearchInterface):
    """Base class for search classes.

    Implements the run() function, which will perform the search.

    Child classes should define values for the various abstract properties this
    class inherits, relevant to the documents the child class is searching over.
    """

    total: int = dfield(default=0, init=False)
    hits: list[AttrDict] = dfield(default_factory=list, init=False)
    results: list[dict] = dfield(default_factory=list, init=False)
    last_key: int | slice | None = dfield(default=None, init=False)

    query: str = ""
    default_operator: str = "AND"
    parse_query: bool = dfield(default=True, init=False)

    def __len__(self):
        return self.total

    @overload
    def __getitem__(self, key: int) -> dict:
        pass

    @overload
    def __getitem__(self, key: slice) -> list[dict]:
        pass

    def __getitem__(self, key):
        if self.last_key is None or self.last_key != key:
            self.run(key=key)
        if isinstance(key, int):
            # if key is an int, then self.results will be a list containing a single result
            # return the result, rather than a 1-length list
            return self.results[0]
        return self.results

    def build_query(self):
        """Build a query to search over a specific set of documents."""
        parsed = None

        if self.parse_query:
            try:
                parsed = Parser(self.query)
            except ParseException:
                pass

        if not parsed:
            parsed = TermToken(self.query)

        return parsed.elastic_query(
            {
                "fields": self.get_fields(),
                "settings": self.get_settings(),
            }
        )

    def build_traditional_query_with_filters(self, strict_matching=False):
        """Build traditional query with filters applied.

        Args:
            strict_matching: If True, apply strict matching rules based on query length
        """
        # Check if this query uses field operators that need query_string
        has_field_operators = ":" in self.query and (
            any(f"{field}:" in self.query for field in self.get_advanced_query_field_names()) or
            any(f"{field.split('^')[0]}:" in self.query for field in self.get_fields())
        )

        if has_field_operators:
            # Use query_string for field operator syntax
            query = DSLQ(
                "query_string",
                query=self.query,
                fields=self.get_fields()
            )
        elif not strict_matching or not self.query or not self.query.strip():
            # Use parser-based query for advanced syntax or when not strict
            parsed = None
            if self.parse_query:
                try:
                    parsed = Parser(self.query)
                except ParseException:
                    pass
            if not parsed:
                parsed = TermToken(self.query)

            query = parsed.elastic_query({
                "fields": self.get_fields(),
                "settings": self.get_settings(),
            })
        else:
            # Use strict matching based on query length
            query_terms = self.query.strip().split()
            term_count = len(query_terms)

            # Check if this is a conversational query (starts with question words)
            conversational_starters = ['how', 'why', 'what', 'when', 'where', 'who', 'which', 'can', 'could', 'should', 'would']
            is_conversational = any(self.query.lower().startswith(word) for word in conversational_starters)

            if term_count == 1:
                # Single term - use normal parser-based matching
                return self.build_traditional_query_with_filters(strict_matching=False)
            elif term_count == 2:
                # 2 terms - require 100% match (AND operator)
                query = DSLQ(
                    "simple_query_string",
                    query=self.query,
                    fields=self.get_fields(),
                    default_operator="AND",
                    flags="PHRASE"
                )
            elif term_count == 3:
                # 3 terms - require 66% match (minimum 2 out of 3)
                query = DSLQ(
                    "simple_query_string",
                    query=self.query,
                    fields=self.get_fields(),
                    minimum_should_match="66%",
                    flags="PHRASE"
                )
            elif term_count == 4:
                # 4 terms - require 50% match (minimum 2 out of 4)
                query = DSLQ(
                    "simple_query_string",
                    query=self.query,
                    fields=self.get_fields(),
                    minimum_should_match="50%",
                    flags="PHRASE"
                )
            # 5+ terms - adjust strictness based on query type
            elif is_conversational:
                # Conversational queries: be more lenient, don't require phrase matching
                query = DSLQ(
                    "simple_query_string",
                    query=self.query,
                    fields=self.get_fields(),
                    minimum_should_match="30%",  # More lenient for conversational queries
                    # No PHRASE flag - allow terms to match in any order
                )
            else:
                # Technical queries: maintain stricter matching
                query = DSLQ(
                    "simple_query_string",
                    query=self.query,
                    fields=self.get_fields(),
                    minimum_should_match="40%",  # Keep stricter for technical queries
                    flags="PHRASE"  # Require phrase matching for technical precision
                )

        return self._apply_filters_to_query(query)

    def build_semantic_query_with_filters(self):
        """Build semantic query with filters applied."""
        semantic_fields = self.get_semantic_fields()
        if not semantic_fields:
            return DSLQ("match_none")

        semantic_queries = [
            DSLQ("semantic", field=field_name, query=self.query)
            for field_name in semantic_fields
        ]

        # Combine semantic queries
        combined_semantic = DSLQ("bool", should=semantic_queries, minimum_should_match=1)

        # Apply base filters
        return self._apply_filters_to_query(combined_semantic)

    def build_hybrid_rrf_query(self):
        """Build RRF hybrid query combining traditional and semantic search with quality filtering."""

        from kitsune.search.search import RRFQuery

        # Get search quality settings with defaults
        rrf_window_size = getattr(settings, 'SEARCH_RRF_WINDOW_SIZE', 50)
        rrf_rank_constant = getattr(settings, 'SEARCH_RRF_RANK_CONSTANT', 60)
        strict_relevance = getattr(settings, 'SEARCH_STRICT_RELEVANCE', True)

        # Build traditional query with stricter matching if enabled
        traditional_query = self.build_traditional_query_with_filters(strict_matching=strict_relevance)

        # Build semantic query (quality filtering applied during result processing)
        semantic_query = self.build_semantic_query_with_filters()

        rrf_query = {
            "retriever": {
                "rrf": {
                    "retrievers": [
                        {"standard": {"query": traditional_query.to_dict()}},
                        {"standard": {"query": semantic_query.to_dict()}}
                    ],
                    "rank_window_size": rrf_window_size,
                    "rank_constant": rrf_rank_constant
                }
            }
        }
        return RRFQuery(rrf_query)

    def get_semantic_fields(self):
        """Return list of semantic fields for this search. Override in subclasses."""
        return []

    def _apply_filters_to_query(self, query):
        """Apply base filters to a query. Override in subclasses for specific behavior."""
        if hasattr(self, 'get_base_filters'):
            return DSLQ("bool", filter=self.get_base_filters(), must=query)
        return query

    def get_advanced_query_field_names(self):
        """Return list of field names that can be used in advanced queries. Override in subclasses."""
        return []

    def is_advanced_query(self, token=None):
        """Check if query uses advanced search syntax."""
        if token is None:
            if not self.query or not self.query.strip():
                return False

            # Quick check for field operators (field:value syntax)
            if ":" in self.query:
                # Check if it's a field operator by looking for known field prefixes
                field_names = self.get_advanced_query_field_names()
                for field in field_names:
                    if f"{field}:" in self.query:
                        return True

                # Also check for locale-aware field names (e.g., title.en-US:, content.fr:)
                # Get all possible field combinations from get_fields()
                if hasattr(self, 'get_fields'):
                    search_fields = self.get_fields()
                    for search_field in search_fields:
                        # Extract base field name (remove boost like ^15)
                        clean_field = search_field.split('^')[0]
                        if f"{clean_field}:" in self.query:
                            return True

            # Check for quoted strings (exact match syntax)
            if '"' in self.query:
                return True

            try:
                parsed = Parser(self.query)
                return self.is_advanced_query(parsed.parsed)
            except ParseException:
                return False

        # Advanced operators and tokens

        if isinstance(
            token, FieldOperator | AndOperator | OrOperator | NotOperator | RangeToken | ExactToken
        ):
            return True

        # SpaceOperator may contain advanced tokens
        if isinstance(token, SpaceOperator):
            return any(self.is_advanced_query(arg) for arg in token.arguments)

        return False

    def run(self, key: int | slice = slice(0, settings.SEARCH_RESULTS_PER_PAGE)) -> Self:
        """Perform search, placing the results in `self.results`, and the total
        number of results (across all pages) in `self.total`. Chainable."""

        from kitsune.search.search import RRFQuery

        filter_or_query = self.get_filter()
        if isinstance(filter_or_query, RRFQuery):
            client = es_client()

            if isinstance(key, slice):
                start = key.start or 0
                stop = key.stop or settings.SEARCH_RESULTS_PER_PAGE
                size = stop - start
            else:
                start = key
                size = 1

            rrf_body = filter_or_query.to_dict()
            rrf_body["from"] = start
            rrf_body["size"] = size

            # Workaround for ES 9.0.2 RRF+highlighting bug
            highlight_fields = {}
            for field, options in self.get_highlight_fields_options():
                # Convert fvh options to plain highlighter for compatibility
                rrf_options = options.copy()
                if rrf_options.get("type") == "fvh":
                    rrf_options["type"] = "plain"
                    # Remove fvh-specific options that aren't supported by plain highlighter
                    rrf_options.pop("boundary_scanner", None)
                highlight_fields[field] = rrf_options

            try:
                result = client.search(
                    index=self.get_index(),
                    body=rrf_body,
                    **settings.ES_SEARCH_PARAMS
                )

                require_text_match = getattr(settings, 'SEARCH_REQUIRE_TEXT_MATCH', True)

                if result["hits"]["hits"] and (highlight_fields or require_text_match):
                    doc_ids = [hit["_id"] for hit in result["hits"]["hits"]]

                    locale = getattr(self, 'locale', 'en-US')
                    filter_highlight_body = {
                        "query": {
                            "bool": {
                                "must": [
                                    {"ids": {"values": doc_ids}},
                                    # Include the original text query for both filtering and highlighting
                                    {"multi_match": {
                                        "query": self.query,
                                        "fields": list(highlight_fields.keys()) if highlight_fields else [
                                            f"content.{locale}",
                                            f"title.{locale}",
                                            f"summary.{locale}"
                                        ]
                                    }}
                                ]
                            }
                        },
                        "size": len(doc_ids),
                        "_source": False
                    }
                    if highlight_fields:
                        filter_highlight_body["highlight"] = {"fields": highlight_fields}

                    filter_highlight_result = client.search(
                        index=self.get_index(),
                        body=filter_highlight_body,
                        **settings.ES_SEARCH_PARAMS
                    )

                    text_matching_ids = {hit["_id"] for hit in filter_highlight_result["hits"]["hits"]}
                    highlights_by_id = {}
                    if highlight_fields:
                        for hit in filter_highlight_result["hits"]["hits"]:
                            if "highlight" in hit:
                                highlights_by_id[hit["_id"]] = hit["highlight"]

                    if require_text_match:
                        filtered_hits = []
                        for hit in result["hits"]["hits"]:
                            if hit["_id"] in text_matching_ids:
                                if hit["_id"] in highlights_by_id:
                                    hit["highlight"] = highlights_by_id[hit["_id"]]
                                filtered_hits.append(hit)
                        result["hits"]["hits"] = filtered_hits
                    else:
                        for hit in result["hits"]["hits"]:
                            if hit["_id"] in highlights_by_id:
                                hit["highlight"] = highlights_by_id[hit["_id"]]

            except RequestError as e:
                if self.parse_query:
                    self.parse_query = False
                    return self.run(key)
                raise e

            # RRF scores are inherently lower than traditional BM25 scores, so use a lower threshold
            rrf_min_score = getattr(settings, 'SEARCH_RRF_MIN_SCORE_THRESHOLD', 0.01)
            self.hits = []

            for hit in result["hits"]["hits"]:
                hit_score = hit.get("_score", 0)

                if hit_score < rrf_min_score:
                    continue

                attr_hit = AttrDict(hit["_source"])
                attr_hit.meta = AttrDict({
                    "id": hit["_id"],
                    "score": hit_score,
                    "index": hit["_index"]
                })
                if "highlight" in hit:
                    attr_hit.meta.highlight = AttrDict(hit["highlight"])
                self.hits.append(attr_hit)

            self.last_key = key
            # Use filtered hit count to prevent pagination issues
            self.total = len(self.hits)
            self.results = [self.make_result(hit) for hit in self.hits]
        else:
            search = DSLSearch(using=es_client(), index=self.get_index()).params(
                **settings.ES_SEARCH_PARAMS
            )

            search = search.query(filter_or_query)
            for highlight_field, options in self.get_highlight_fields_options():
                search = search.highlight(highlight_field, **options)
            search = search[key]
            try:
                result = search.execute()
            except RequestError as e:
                if self.parse_query:
                    self.parse_query = False
                    return self.run(key)
                raise e

            self.hits = result.hits
            self.last_key = key

            self.total = self.hits.total.value  # type: ignore
            self.results = [self.make_result(hit) for hit in self.hits]

        return self


class SumoSearchPaginator(DjPaginator):
    """
    Paginator for `SumoSearch` classes.

    Inherits from the default django paginator with a few adjustments. The default paginator
    attempts to call len() on the `object_list` first, and then query for an individual page.

    However, since elasticsearch returns the total number of results at the same time as querying
    for a single page, we can remove an extra query by only doing len() based operations after
    querying for a page.

    Because of this, the `orphans` argument won't work.
    """

    @property
    def count(self):
        """Return the total number of objects, updating dynamically after search runs."""
        return len(self.object_list)

    def pre_validate_number(self, number):
        """
        Validate the given 1-based page number, without checking if the number is greater than
        the total number of pages.
        """
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger(_("That page number is not an integer"))
        if number < 1:
            raise EmptyPage(_("That page number is less than 1"))
        return number

    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        # first validate the number is an integer >= 1
        number = self.pre_validate_number(number)

        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        page = self._get_page(self.object_list[bottom:top], number, self)

        # now we have the total, do the full validation of the number
        self.validate_number(number)
        return page
