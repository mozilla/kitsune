from pyparsing import (
    Literal,
    ParseException,
    ParserElement,
    Regex,
    White,
    Word,
    alphas,
    dblQuotedString,
    infixNotation,
    opAssoc,
    removeQuotes,
    stringEnd,
)

from .operators import AndOperator, FieldOperator, NotOperator, OrOperator, SpaceOperator
from .tokens import ExactToken, RangeToken, TermToken

_MAX_NESTING_DEPTH = 10

# Avoid repeated backtracking through nested Boolean expressions.
ParserElement.enable_packrat()

# convenience:
# DRY things up
_colon = Literal(":")
_token = Regex(r"[^\(\)\s]+")  # everything but chars which conflict with the below operators
_arg = Word(alphas + "_.-")
_value = (
    Regex(r"\"[^\"]+\"") | Regex(r"\([^\(\)]+\)")  # match phrase surrounded with "" or ()
).set_parse_action(removeQuotes) | _token

# operators:
# a special kind of token which can be nested with any other token (including operators)
# e.g. NOT a AND field:b:(c OR d)
_field = Literal("field:") + _arg("field") + _colon
_not = Literal("NOT")
_and = Literal("AND")
_or = Literal("OR")
_space = White()

# basic tokens:
# tokens which cannot be nested with another token
# e.g. "range:date:lt:(2019 OR 2020)" makes no sense
_range = (
    Literal("range:") + _arg("field") + _colon + _arg("operator") + _colon + _value("value")
).add_parse_action(RangeToken)
_exact = (Literal("exact:") + _arg("field") + _colon + _value("value")).add_parse_action(
    ExactToken
)
_term = (dblQuotedString | _token)("term").add_parse_action(TermToken)

# the overall expression:
search_term = _range | _exact | _term
search_expression = (
    infixNotation(
        search_term,
        [
            (_field, 1, opAssoc.RIGHT, FieldOperator),
            (_not, 1, opAssoc.RIGHT, NotOperator),
            (_and, 2, opAssoc.LEFT, AndOperator),
            (_or, 2, opAssoc.LEFT, OrOperator),
            (_space, 2, opAssoc.LEFT, SpaceOperator),
        ],
    )
    + stringEnd
)


class Parser:
    def __init__(self, query):
        depth = 0
        quoted = False
        escaped = False
        for position, character in enumerate(query):
            if escaped:
                escaped = False
            elif quoted and character == "\\":
                escaped = True
            elif character == '"':
                quoted = not quoted
            elif not quoted and character == "(":
                depth += 1
                if depth > _MAX_NESTING_DEPTH:
                    raise ParseException(query, position, "query nesting is too deep")
            elif not quoted and character == ")":
                depth = max(0, depth - 1)
        try:
            self.parsed = search_expression.parse_string(query)[0]
        except RecursionError as exc:
            # The lightweight check above cannot exactly reproduce pyparsing's treatment of
            # malformed quotes. Keep parser complexity failures on the existing fallback path.
            raise ParseException(query, 0, "query nesting is too deep") from exc

    def __repr__(self):
        """Create a string representation of this parsed string suitable for debugging."""
        return repr(self.parsed)

    def elastic_query(self, context=None):
        """Create an elastic query out of this parsed string."""
        context = dict(context or {})
        context.setdefault("fields", {})
        context.setdefault("settings", {})
        return self.parsed.elastic_query(context)
