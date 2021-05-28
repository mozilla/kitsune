from abc import ABC, abstractmethod

from elasticsearch_dsl import Q as DSLQ


class BaseToken(ABC):
    def __init__(self, tokens):
        self.tokens = tokens

    @abstractmethod
    def __repr__(self):
        """Create a string representation of this token suitable for debugging."""
        pass

    @abstractmethod
    def elastic_query(self, context):
        """Create an elastic query out of this token."""
        pass


class TermToken(BaseToken):
    def __init__(self, tokens):
        if isinstance(tokens, str):
            self.term = tokens
        else:
            self.term = tokens.term

    def __repr__(self):
        return fr"t{repr(self.term)}"

    def __iadd__(self, other):
        if type(other) is not type(self):
            raise TypeError
        self.term += " " + other.term
        return self

    def elastic_query(self, context):
        return DSLQ(
            "simple_query_string",
            query=self.term,
            default_operator="AND",
            fields=context["fields"],
            flags="PHRASE",
        )


class RangeToken(BaseToken):
    def __repr__(self):
        return r"RangeToken(field={}, operator={}, value={})".format(
            repr(self.tokens.field), repr(self.tokens.operator), repr(self.tokens.value)
        )

    def elastic_query(self, context):
        field = self.tokens.field
        allowed = context["settings"].get("range_allowed", [])
        if field in allowed:
            return DSLQ("range", **{field: {self.tokens.operator: self.tokens.value}})
        else:
            return DSLQ("match_none")


class ExactToken(BaseToken):
    def __repr__(self):
        return r"ExactToken(field={}, value={})".format(
            repr(self.tokens.field), repr(self.tokens.value)
        )

    def elastic_query(self, context):
        field = self.tokens.field
        value = self.tokens.value
        values = None

        mappings = context["settings"].get("exact_mappings", [])
        if field in mappings:
            # map field
            mapping = mappings[field]
            field = mapping["field"]
            # map value
            if "dict" in mapping:
                value = mapping["dict"].get(value, value)

        return DSLQ("terms", **{field: values or [value]})
