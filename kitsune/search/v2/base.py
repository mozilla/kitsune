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
            # Ovewrite the value if there is a specific method implented for the specific field
            if prepare_method is not None:
                value = prepare_method(instance)
            else:
                value = getattr(instance, f)

            # Assign values to each field. Assign a dictionary to Objects
            if isinstance(doc_mapping.resolve_field(f), field.Object):
                locale = obj.prepare_locale(instance)
                if locale and value:
                    obj[f] = {locale: value}
                # We  populate non-locale object fields here
            else:
                setattr(obj, f, value)

        obj.meta.id = instance.id
        obj.indexed_on = timezone.now()

        return obj

    def prepare_locale(self, instance):
        """Return the locale of an object if exists."""
        if getattr(instance, "locale"):
            return instance.locale
        return ""
