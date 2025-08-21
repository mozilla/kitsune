from abc import ABC, abstractmethod

from elasticsearch.dsl import Q as DSLQ


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
        return rf"t{self.term!r}"

    def __iadd__(self, other):
        if type(other) is not type(self):
            raise TypeError
        self.term += " " + other.term
        return self

    def elastic_query(self, context):
        # Split the query to count terms for minimum match calculation
        terms = self.term.split()

        query_params = {
            "query": self.term,
            "default_operator": "OR",
            "fields": context["fields"],
        }

        # Add minimum_should_match for multi-term queries to improve quality
        # For 2-3 terms: require 60% match, 4+ terms: require 50% match
        if len(terms) >= 2:
            if len(terms) <= 3:
                query_params["minimum_should_match"] = "60%"
            else:
                query_params["minimum_should_match"] = "50%"

        return DSLQ("simple_query_string", **query_params)


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
