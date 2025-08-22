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

        # Check for single-term gibberish patterns
        if len(terms) == 1:
            term = terms[0].lower()
            # Block obvious gibberish patterns
            if self._is_likely_gibberish(term):
                # Return a query that matches nothing
                return DSLQ("bool", must_not=DSLQ("match_all"))

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

    def _is_likely_gibberish(self, term):
        """Detect if a single term appears to be gibberish."""
        # Skip very short terms (could be abbreviations)
        if len(term) < 4:
            return False

        # Skip common patterns that might be legitimate
        if term.isdigit() or term.startswith(('http', 'www', 'ftp')):
            return False

        # Check for excessive repeated characters (like "asdfasdfadad")
        if len(term) >= 8:
            # Count repeated 2-character patterns
            pattern_repeats = 0
            for i in range(len(term) - 3):
                if term[i:i+2] == term[i+2:i+4]:
                    pattern_repeats += 1

            # If more than 30% of the string is repeated 2-char patterns, likely gibberish
            if pattern_repeats / (len(term) - 3) > 0.3:
                return True

        # Check for keyboard patterns (qwerty, asdf, etc.)
        keyboard_patterns = ['qwerty', 'asdf', 'zxcv', 'qaz', 'wsx', 'edc']
        for pattern in keyboard_patterns:
            if pattern in term or pattern[::-1] in term:  # Also check reverse
                return True

        # Check for excessive consonant/vowel imbalance (very basic heuristic)
        vowels = 'aeiou'
        vowel_count = sum(1 for c in term if c in vowels)
        consonant_count = sum(1 for c in term if c.isalpha() and c not in vowels)

        # If less than 10% vowels or more than 90% vowels, likely gibberish
        if consonant_count > 0:
            vowel_ratio = vowel_count / (vowel_count + consonant_count)
            if vowel_ratio < 0.1 or vowel_ratio > 0.9:
                return True

        return False


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
