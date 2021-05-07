from abc import ABC, abstractmethod
from dataclasses import dataclass
from dataclasses import field as dfield
from datetime import datetime
from typing import Union, overload

from django.conf import settings
from django.core.paginator import Paginator as DjPaginator, PageNotAnInteger, EmptyPage
from django.utils import timezone
from django.utils.translation import ugettext as _

from elasticsearch7.exceptions import NotFoundError
from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import InnerDoc, MetaField
from elasticsearch_dsl import Search as DSLSearch
from elasticsearch_dsl import field
from elasticsearch_dsl.utils import AttrDict
from pyparsing import ParseException

from kitsune.search.config import (
    DEFAULT_ES7_CONNECTION,
    DEFAULT_ES7_REFRESH_INTERVAL,
    UPDATE_RETRY_ON_CONFLICT,
)
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.v2.parser import Parser
from kitsune.search.v2.parser.tokens import TermToken


class SumoDocument(DSLDocument):
    """Base class with common methods for all the different documents."""

    indexed_on = field.Date()

    class Meta:
        # ignore fields if they don't exist in the mapping
        dynamic = MetaField("false")

    def __init_subclass__(cls, **kwargs):
        """Automatically set up each subclass' Index attribute."""
        super().__init_subclass__(**kwargs)

        cls.Index.using = DEFAULT_ES7_CONNECTION

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
        cls.Index.settings = {"refresh_interval": DEFAULT_ES7_REFRESH_INTERVAL}

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
        name = f'{cls.Index.base_name}_{timestamp.strftime("%Y%m%d%H%M%S")}'
        cls.init(index=name)
        cls._update_alias(cls.Index.write_alias, name)

    @classmethod
    def migrate_reads(cls):
        """Point the read alias at the same index as the write alias."""
        cls._update_alias(cls.Index.read_alias, cls.alias_points_at(cls.Index.write_alias))

    @classmethod
    def _update_alias(cls, alias, new_index):
        client = es7_client()
        old_index = cls.alias_points_at(alias)
        if not old_index:
            client.indices.put_alias(new_index, alias)
        else:
            client.indices.update_aliases(
                {
                    "actions": [
                        {"remove": {"index": old_index, "alias": alias}},
                        {"add": {"index": new_index, "alias": alias}},
                    ]
                }
            )

    @classmethod
    def alias_points_at(cls, alias):
        """Returns the index `alias` points at."""
        try:
            aliased_indices = list(es7_client().indices.get_alias(name=alias))
        except NotFoundError:
            aliased_indices = []

        if len(aliased_indices) > 1:
            raise RuntimeError(
                f"{alias} points at more than one index, something has gone very wrong"
            )

        return aliased_indices[0] if aliased_indices else None

    @classmethod
    @property
    def update_document(cls):
        """Controls if a document should be indexed or updated in ES.

        True: An update action will be performed in ES.
        False: An index action will be performed in ES.
        """
        return False

    @classmethod
    def prepare(cls, instance, parent_id=None, **kwargs):
        """Prepare an object given a model instance.

        parent_id: Supplying a parent_id will ignore any fields which aren't a
        SumoLocaleAware field, and set the meta.id value to the parent_id one.
        """

        obj = cls()

        doc_mapping = obj._doc_type.mapping
        fields = [f for f in doc_mapping]
        fields.remove("indexed_on")
        # Loop through the fields of each object and set the right values

        # check if the instance is suitable for indexing
        # the prepare method of each Document Type can mark an object
        # not suitable for indexing based on criteria defined on each said method
        if not hasattr(instance, "es_discard_doc"):
            for f in fields:

                # This will allow child classes to have their own methods
                # in the form of prepare_field
                prepare_method = getattr(obj, "prepare_{}".format(f), None)
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
                        # set is_dst=False to avoid errors when an ambiguous time is sent:
                        # https://docs.djangoproject.com/en/2.2/ref/utils/#django.utils.timezone.make_aware
                        value = timezone.make_aware(value, is_dst=False).astimezone(timezone.utc)

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
        # overrides it with a deletion. This can happen if the `prpare` method of each
        # document type has marked a document as not suitable for indexing
        if hasattr(self, "es_discard_doc"):
            # Let's try to delete anything that might exist in ES
            action = "delete"

        # Default to index if no action is defined or if it's `save`
        # if we have a bulk update, we need to include the meta info
        # and return the data by calling the to_dict() method of DSL
        payload = self.to_dict(include_meta=is_bulk, skip_empty=False)

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
            return self.delete(**{"ignore": [400, 404]})

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
        if getattr(instance, "locale"):
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

    @abstractmethod
    def get_advanced_settings(self):
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
    def run(self, **kwargs):
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
    last_key: Union[int, slice, None] = dfield(default=None, init=False)

    query: str = ""
    default_operator: str = "AND"

    def __len__(self):
        return self.total

    @overload
    def __getitem__(self, key: int) -> dict:
        ...

    @overload
    def __getitem__(self, key: slice) -> list[dict]:
        ...

    def __getitem__(self, key):
        if self.last_key is None or self.last_key != key:
            self.run(key=key)
        if isinstance(key, int):
            # if key is an int, then self.results will be a list containing a single result
            # return the result, rather than a 1-length list
            return self.results[0]
        return self.results

    def get_advanced_settings(self):
        return {}

    def build_query(self):
        """Build a query to search over a specific set of documents."""
        try:
            parsed = Parser(self.query)
        except ParseException:
            parsed = TermToken(self.query)
        return parsed.elastic_query(
            {
                "fields": self.get_fields(),
                "settings": self.get_advanced_settings(),
            }
        )

    def run(self, key: Union[int, slice] = slice(0, settings.SEARCH_RESULTS_PER_PAGE)):
        """Perform search, placing the results in `self.results`, and the total
        number of results (across all pages) in `self.total`. Chainable."""

        search = DSLSearch(using=es7_client(), index=self.get_index()).params(
            **settings.ES7_SEARCH_PARAMS
        )

        # add the search class' filter
        search = search.query(self.get_filter())
        # add highlights for the search class' highlight_fields
        for highlight_field, options in self.get_highlight_fields_options():
            search = search.highlight(highlight_field, **options)
        # slice search
        search = search[key]

        # perform search
        self.hits = search.execute().hits
        self.last_key = key

        self.total = self.hits.total.value
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
