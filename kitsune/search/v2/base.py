from abc import ABC, abstractmethod
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import InnerDoc, MetaField
from elasticsearch_dsl import Search as DSLSearch
from elasticsearch_dsl import field

from kitsune.search import HIGHLIGHT_TAG, SNIPPET_LENGTH
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.config import UPDATE_RETRY_ON_CONFLICT


class SumoDocument(DSLDocument):
    """Base class with common methods for all the different documents."""

    indexed_on = field.Date()

    class Meta:
        # ignore fields if they don't exist in the mapping
        dynamic = MetaField("false")

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


class SumoSearch(ABC):
    """Base class for search classes.

    Implements the run() function, which will perform the search.

    Child classes should define values for the various abstract properties this
    class has, relevant to the documents the child class is searching over.
    """

    def __init__(self, **kwargs):
        self.results_per_page = settings.SEARCH_RESULTS_PER_PAGE
        self.hits = []
        self.total = 0
        self.results = []

    @abstractmethod
    def get_index(self):
        """The index or comma-seperated indices to search over."""
        pass

    @abstractmethod
    def get_fields(self):
        """An array of fields to search over."""
        pass

    @abstractmethod
    def get_highlight_fields(self):
        """An array of fields to highlight."""
        pass

    @abstractmethod
    def get_filter(self):
        """A query which filters for all documents to be searched over."""
        pass

    @abstractmethod
    def make_result(self, hit):
        """Takes a hit and returns a result dictionary."""
        pass

    def run(self, query, page=1, default_operator="AND"):
        """Perform search, placing the results in `self.results`, and the total
        number of results (across all pages) in `self.total`. Chainable."""

        search = DSLSearch(using=es7_client(), index=self.get_index())

        # add the search class' filter
        search = search.query("bool", filter=self.get_filter())

        # add query, search over the search class' fields
        search = search.query(
            "simple_query_string",
            query=query,
            default_operator=default_operator,
            fields=self.get_fields(),
        )

        # add highlights for the search class' highlight_fields
        search = search.highlight(
            *self.get_highlight_fields(),
            type="fvh",
            # order highlighted fragments by their relevance:
            order="score",
            # only get one fragment per field:
            number_of_fragments=1,
            # split fragments at the end of sentences:
            boundary_scanner="sentence",
            # return fragments roughly this size:
            fragment_size=SNIPPET_LENGTH,
            # add these tags before/after the highlighted sections:
            pre_tags=[f"<{HIGHLIGHT_TAG}>"],
            post_tags=[f"</{HIGHLIGHT_TAG}>"],
        )

        # do pagination
        start = (page - 1) * self.results_per_page
        search = search[start : start + self.results_per_page]

        # perform search
        self.hits = search.execute().hits

        self.total = self.hits.total.value if self.hits else 0
        self.results = [self.make_result(hit) for hit in self.hits]

        return self
