from django.test import SimpleTestCase
from parameterized import parameterized
from pyparsing import ParseException

from kitsune.search.v2.parser import Parser


class ParserTests(SimpleTestCase):
    @parameterized.expand(
        [
            ("firefox crashes", "SpaceOperator(t'firefox', t'crashes')"),
            ("  firefox   crashes   ", "SpaceOperator(t'firefox', t'crashes')"),
            ("更新 firefox", "SpaceOperator(t'更新', t'firefox')"),
            ("(a) b", "SpaceOperator(t'a', t'b')"),
            ("(a b)", "SpaceOperator(t'a', t'b')"),
            ("a OR b AND c", "OrOperator(t'a', AndOperator(t'b', t'c'))"),
            ("a OR b OR c", "OrOperator(t'a', t'b', t'c')"),
            ("a OR OR b", "SpaceOperator(OrOperator(t'a', t'OR'), t'b')"),
            ("NOT NOT a", "NotOperator(NotOperator(t'a'))"),
            ("NOT a NOT", "SpaceOperator(NotOperator(t'a'), t'NOT')"),
            ("field:a:b", "FieldOperator(t'b', field='a')"),
            ("field:a:NOT b", "SpaceOperator(FieldOperator(t'NOT', field='a'), t'b')"),
            ("field:a:(NOT b)", "FieldOperator(NotOperator(t'b'), field='a')"),
            ('NOT "a b"', "NotOperator(t'\"a b\"')"),
            ('NOT "更新 firefox"', "NotOperator(t'\"更新 firefox\"')"),
            ('NOT "a b', "SpaceOperator(NotOperator(t'\"a'), t'b')"),
            ('"NOT a"', "t'\"NOT a\"'"),
            ("not a", "SpaceOperator(t'not', t'a')"),
            (
                "range:a:b:c d",
                "SpaceOperator(RangeToken(field='a', operator='b', value='c'), t'd')",
            ),
            ("range:a:b", "t'range:a:b'"),
            ('exact:a:"NOT b" c', "SpaceOperator(ExactToken(field='a', value='NOT b'), t'c')"),
            ('exact:a:"NOT b', "SpaceOperator(ExactToken(field='a', value='\"NOT'), t'b')"),
            ("exact:a:(NOT b) c", "SpaceOperator(ExactToken(field='a', value='NOT b'), t'c')"),
        ]
    )
    def test_parser(self, query, expected):
        self.assertEquals(repr(Parser(query)), expected)

    @parameterized.expand(
        [
            ("(a b", ""),
            ("exact:a:(NOT b", ""),
        ]
    )
    def test_exceptions(self, query, expected):
        with self.assertRaises(ParseException):
            repr(Parser(query))
