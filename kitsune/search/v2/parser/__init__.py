from pyparsing import (
    Word,
    alphas,
    Literal,
    White,
    Regex,
    infixNotation,
    opAssoc,
    stringEnd,
)

from .operators import FieldOperator, NotOperator, AndOperator, OrOperator, SpaceOperator
from .tokens import TermToken, RangeToken, ExactToken

# convenience:
# DRY things up
_colon = Literal(":")
_arg = Word(alphas + "_")

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
_token = Regex(r"[^\(\)\s]+")  # everything but chars which conflict with the above operators
_range = (
    Literal("range:") + _arg("field") + _colon + _arg("operator") + _colon + _token("value")
).addParseAction(RangeToken)
_exact = (Literal("exact:") + _arg("field") + _colon + _token("value")).addParseAction(ExactToken)
_term = _token("term").addParseAction(TermToken)

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


class Parser(object):
    def __init__(self, search):
        self.query = search.query
        self.context = {"fields": search.get_fields(), "settings": search.get_advanced_settings()}

    def elastic_query(self):
        return search_expression.parseString(self.query)[0].elastic_query(self.context)
