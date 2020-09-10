from django.utils import timezone

from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import field


class SumoDocument(DSLDocument):
    """Base class with common methods for all the different documents."""

    indexed_on = field.Date()

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
            value = cls.get_field_value(f, instance, prepare_method)

            # Assign values to each field. Assign a dictionary to multi locale Objects
            field_type = doc_mapping.resolve_field(f)
            if isinstance(field_type, field.Object) and "en-US" in field_type._mapping:
                locale = obj.prepare_locale(instance)
                if locale and value:
                    obj[f] = {locale: value}
            else:
                setattr(obj, f, value)

        obj.meta.id = instance.id
        obj.indexed_on = timezone.now()

        return obj

    @classmethod
    def get_field_value(cls, field, instance, prepare_method):
        """Allow child classes to define their own logic for getting field values."""
        if prepare_method is not None:
            return prepare_method(instance)
        else:
            return getattr(instance, field)

    def prepare_locale(self, instance):
        """Return the locale of an object if exists."""
        if getattr(instance, "locale"):
            return instance.locale
        return ""
