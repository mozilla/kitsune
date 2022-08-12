from django.test import SimpleTestCase, TestCase
from parameterized import parameterized
from pyparsing import ParseException
from elasticsearch_dsl import Q
from elasticsearch_dsl.query import SimpleQueryString as S, Bool as B

from kitsune.search.parser import Parser


class ElasticQueryContainsMixin(object):
    def assertNestedDictContains(self, superset, subset):
        assert type(superset) is type(subset)
        if isinstance(superset, dict):
            for key, value in subset.items():
                assert key in superset
                super_value = superset[key]
                self.assertNestedDictContains(super_value, value)
        elif isinstance(superset, list):
            self.assertEqual(len(superset), len(subset))
            try:
                sorted_superset = sorted(superset)
                sorted_subset = sorted(subset)
            except TypeError:
                sorted_superset = superset
                sorted_subset = subset
            for super_value, value in zip(sorted_superset, sorted_subset):
                self.assertNestedDictContains(super_value, value)
        else:
            self.assertEqual(superset, subset)

    def assertElasticQueryContains(self, query, contains):
        self.assertNestedDictContains(query.to_dict(), contains.to_dict())


class TestElasticQueryContainsMixin(SimpleTestCase, ElasticQueryContainsMixin):
    @parameterized.expand(
        [
            ({"g": "h"}, False),
            ({"g": "x"}, True),
            ({"x": "x"}, True),
            ({"a": ["b"]}, True),
            ({"a": ["b", {"e": "f"}]}, False),
            ({"a": ["b", {"x": "x"}]}, True),
        ]
    )
    def test_assertNestedDictContains_raises(self, subset, raises):
        superset = {
            "a": ["b", {"c": "d", "e": "f"}],
            "g": "h",
        }
        if raises:
            with self.assertRaises(AssertionError):
                self.assertNestedDictContains(superset, subset)
        else:
            self.assertNestedDictContains(superset, subset)


class ParserTests(SimpleTestCase, ElasticQueryContainsMixin):
    @parameterized.expand(
        [
            ("firefox crashes", "SpaceOperator(t'firefox', t'crashes')"),
            ("  firefox   crashes   ", "SpaceOperator(t'firefox', t'crashes')"),
            ("更新 firefox", "SpaceOperator(t'更新', t'firefox')"),
            ("(a) b", "SpaceOperator(t'a', t'b')"),
            ("(a b)", "SpaceOperator(t'a', t'b')"),
            ("a OR b AND c", "OrOperator(t'a', AndOperator(t'b', t'c'))"),
            ("a OR b OR c", "OrOperator(t'a', t'b', t'c')"),
            ("a OR (b OR c)", "OrOperator(t'a', OrOperator(t'b', t'c'))"),
            ("a OR OR b", "SpaceOperator(OrOperator(t'a', t'OR'), t'b')"),
            ("NOT NOT a", "NotOperator(NotOperator(t'a'))"),
            ("NOT a NOT", "SpaceOperator(NotOperator(t'a'), t'NOT')"),
            ("field:a:b", "FieldOperator(t'b', field='a')"),
            ("field:a_b.c:d", "FieldOperator(t'd', field='a_b.c')"),
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
        self.assertEqual(repr(Parser(query)), expected)

    @parameterized.expand(
        [
            ("(a b", ""),
            ("exact:a:(NOT b", ""),
        ]
    )
    def test_exceptions(self, query, expected):
        with self.assertRaises(ParseException):
            repr(Parser(query))

    @parameterized.expand(
        [
            ("a b", S(query="a b")),
            ('"a b" c "d"', S(query='"a b" c "d"')),
            ("NOT a", B(must_not=S(query="a"))),
            ("a NOT b", B(must=[S(query="a"), B(must_not=S(query="b"))])),
            ("a AND b AND c", B(must=[S(query="a"), S(query="b"), S(query="c")])),
            ("a OR b AND c", B(should=[S(query="a"), B(must=[S(query="b"), S(query="c")])])),
        ]
    )
    def test_elastic_query(self, query, expected):
        elastic_query = Parser(query).elastic_query()
        self.assertElasticQueryContains(elastic_query, expected)

    @parameterized.expand(
        [
            ("field:a:b", S(query="b", fields=["a"])),
            ("field:mapped_x:a", S(query="a", fields=["x"])),
            (
                "field:mapped_y:(a OR b)",
                B(should=[S(query="a", fields=["y"]), S(query="b", fields=["y"])]),
            ),
            ("field:mapped_multiple:a", S(query="a", fields=["x", "y"])),
        ]
    )
    def test_field_operator_elastic_query(self, query, expected):
        field_mappings = {
            "mapped_x": "x",
            "mapped_y": "y",
            "mapped_multiple": ["x", "y"],
        }
        elastic_query = Parser(query).elastic_query(
            {"settings": {"field_mappings": field_mappings}}
        )
        self.assertElasticQueryContains(elastic_query, expected)

    @parameterized.expand(
        [
            ("range:a:b:c", Q("range", a={"b": "c"})),
            ("range:x:y:z", Q("match_none")),
        ]
    )
    def test_range_token_elastic_query(self, query, expected):
        range_allowed = ["a"]
        elastic_query = Parser(query).elastic_query({"settings": {"range_allowed": range_allowed}})
        self.assertElasticQueryContains(elastic_query, expected)


class ExactTokenTests(TestCase, ElasticQueryContainsMixin):
    @parameterized.expand(
        [
            ("exact:a:b", Q("terms", a=["b"])),
            ("exact:b:c", Q("terms", x=["d"])),
        ]
    )
    def test_exact(self, query, expected):
        exact_mappings = {
            "b": {
                "dict": {"c": "d"},
                "field": "x",
            },
        }
        elastic_query = Parser(query).elastic_query(
            {"settings": {"exact_mappings": exact_mappings}}
        )
        self.assertElasticQueryContains(elastic_query, expected)
