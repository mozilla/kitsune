from abc import ABC, abstractmethod

from django.apps import apps
from elasticsearch_dsl import Q


class BaseToken(ABC):
    def __init__(self, tokens):
        self.tokens = tokens

    def __str__(self):
        return str("".join(self.tokens))

    def __repr__(self):
        args = ", ".join([f"{repr(x)}" for x in self.tokens])
        return f"{type(self).__name__}({args})"

    @abstractmethod
    def elastic_query(self, context):
        """Create an elastic query out of this token."""
        pass


class TermToken(BaseToken):
    def __repr__(self):
        return f"t{repr(self.tokens.term)}"

    def __iadd__(self, other):
        if type(other) is not type(self):
            raise TypeError
        self.tokens.term += " " + other.tokens.term
        return self

    def elastic_query(self, context):
        return Q(
            "simple_query_string",
            query=self.tokens.term,
            default_operator="AND",
            fields=context["fields"],
            flags="PHRASE",
        )


class RangeToken(BaseToken):
    def __repr__(self):
        return "RangeToken(field={}, operator={}, value={})".format(
            repr(self.tokens.field), repr(self.tokens.operator), repr(self.tokens.value)
        )

    def elastic_query(self, context):
        return Q("range", **{self.tokens.field: {self.tokens.operator: self.tokens.value}})


class ExactToken(BaseToken):
    def __repr__(self):
        return "ExactToken(field={}, value={})".format(
            repr(self.tokens.field), repr(self.tokens.value)
        )

    def elastic_query(self, context):
        field = self.tokens.field
        value = self.tokens.value
        values = None

        mappings = context["settings"]["exact_mappings"]
        if field in mappings:
            # map field
            mapping = mappings[field]
            field = mapping["field"]
            # map value
            if "model" in mapping:
                model = apps.get_model(mapping["model"])
                results = model._default_manager.filter(**{mapping["column"]: value})
                values = list(results.values_list(mapping["attribute"], flat=True))
            elif "dict" in mapping:
                value = mapping["dict"].get(value, value)

        return Q("terms", **{field: values or [value]})
