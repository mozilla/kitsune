from datetime import datetime

from django.utils import timezone
from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import InnerDoc, MetaField, field


class SumoDocument(DSLDocument):
    """Base class with common methods for all the different documents."""

    indexed_on = field.Date()
    updated_on = field.Date()

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
        fields.remove("updated_on")
        merge_docs = kwargs.pop("merge_docs", False)

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

                # if merge_docs is True and we don't have a SumoLocaleAware field
                # then We need to get the value from the parent
                if merge_docs and instance.parent:
                    value = obj.get_field_value(f, instance.parent, prepare_method)
                setattr(obj, f, value)

        obj.indexed_on = datetime.now(timezone.utc)
        obj.updated_on = datetime.now(timezone.utc)
        obj.meta.id = instance.pk
        if merge_docs and instance.parent:
            obj.meta.id = instance.parent.pk

        return obj

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
