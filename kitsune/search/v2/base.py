from datetime import datetime

from django.utils import timezone
from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import InnerDoc, MetaField, field

from kitsune.wiki.models import Document


class SumoDocument(DSLDocument):
    """Base class with common methods for all the different documents."""

    indexed_on = field.Date()

    class Meta:
        # ignore fields if they don't exist in the mapping
        dynamic = MetaField("false")

    @classmethod
    def prepare(cls, instance, **kwargs):
        """Prepare an object given a model instance.

        merge_docs: Controls whether multiple docements will be merged into the parent one.
        Currently used by the Knowledge Base
        """

        obj = cls()
        doc_mapping = obj._doc_type.mapping
        fields = [f for f in doc_mapping]
        fields.remove("indexed_on")
        # this flag toggles the merging of child docs into parents
        use_parent_obj = (
            isinstance(instance, Document)
            and kwargs.pop("merge_docs", False)
            and instance.parent is not None
        )
        # Loop through the fields of each object and set the right values
        for f in fields:

            # This will allow child classes to have their own methods in the form of prepare_field
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

                if use_parent_obj:
                    value = obj.get_field_value(f, instance.parent, prepare_method)

                setattr(obj, f, value)

        obj.indexed_on = datetime.now(timezone.utc)
        obj.meta.id = instance.pk
        if use_parent_obj:
            obj.meta.id = instance.parent.pk

        return obj

    def to_action(self, action=None, **kwargs):
        """Method to construct the data for save, delete, update operations.

        Useful for bulk operations.
        """

        # Default to index if no action is defined or if it's `save`
        payload = {}
        # if we have a bulk update, we need to include the meta info
        # and return the data by calling the to_dict() method of DSL
        if is_bulk := kwargs.pop("is_bulk", False):
            payload = self.to_dict(include_meta=is_bulk)

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
                payload.update({"_op_type": "update"})
                del payload["_source"]
                return payload
            return self.update(**payload)
        elif action == "delete":
            return self.delete()

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
