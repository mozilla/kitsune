from django.utils import timezone
from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import InnerDoc, field, MetaField


class SumoDocument(DSLDocument):
    """Base class with common methods for all the different documents."""

    indexed_on = field.Date()

    class Meta:
        # ignore fields if they don't exist in the mapping
        dynamic = MetaField("false")

    @classmethod
    def prepare(cls, instance):
        """Prepare an object given a model instance"""
        obj = cls()
        doc_mapping = obj._doc_type.mapping
        fields = [f for f in doc_mapping]
        fields.remove("indexed_on")

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
                if locale and value:
                    obj[f] = {locale: value}
            else:
                setattr(obj, f, value)

        obj.meta.id = instance.pk
        obj.indexed_on = timezone.now()

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
