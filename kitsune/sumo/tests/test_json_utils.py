from django.http import HttpResponse
from django.test.client import RequestFactory
from nose.tools import eq_

from kitsune.sumo.json_utils import jsonp_is_valid
from kitsune.sumo.json_utils import markup_json
from kitsune.sumo.json_utils import template_json
from kitsune.sumo.tests import TestCase


def test_jsonp_is_valid():
    tests = [
        ("callback", True),
        ("validCallback", True),
        ("obj.method", True),
        ("obj.someMethod", True),
        ("arr[1]", True),
        ("arr[12]", True),
        ("alert('xss');foo", False),
        ("eval('nastycode')", False),
        ("someFunc()", False),
        ("x", True),
        ("x123", True),
        ("$", True),
        ("_func", True),
        ("\"></script><script>alert('xss')</script>", False),
        ('">', False),
        ("var x=something;foo", False),
        ("var x=", False),
    ]
    for funcname, expected in tests:
        eq_(jsonp_is_valid(funcname), expected)


def random_view_fun(request, *args, **kwargs):
    return HttpResponse("foo")


jsonified_fun = markup_json(random_view_fun)


class TestMarkupJson(TestCase):
    factory = RequestFactory()

    def test_is_json_false_no_format(self):
        # Note: The request gets mutated by markup_json, so we can test both
        # the request and response after processing the request.
        req = self.factory.get("/")
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, False)
        eq_(resp.status_code, 200)

    def test_is_json_false_wrong_format(self):
        req = self.factory.get("/", {"format": "html"})
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, False)
        eq_(resp.status_code, 200)

    def test_is_json_true(self):
        req = self.factory.get("/", {"format": "json"})
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, True)
        eq_(resp.status_code, 200)

    def test_json_callback_not_is_json(self):
        req = self.factory.get("/")
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, False)
        eq_(req.JSON_CALLBACK, "")
        eq_(resp.status_code, 200)

    def test_json_callback_valid(self):
        req = self.factory.get("/", {"format": "json", "callback": "callback"})
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, True)
        eq_(req.JSON_CALLBACK, "callback")
        eq_(resp.status_code, 200)

    def test_json_callback_invalid(self):
        req = self.factory.get("/", {"format": "json", "callback": '">'})
        resp = jsonified_fun(req)
        eq_(resp.status_code, 400)
        eq_(resp.content, b'{"error": "Invalid callback function."}')

    def test_content_type_not_json(self):
        req = self.factory.get("/")
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, False)
        eq_(req.CONTENT_TYPE, "text/html")
        eq_(resp.status_code, 200)

    def test_content_type_json(self):
        req = self.factory.get("/", {"format": "json"})
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, True)
        eq_(req.CONTENT_TYPE, "application/json")
        eq_(resp.status_code, 200)

    def test_content_type_jsonp(self):
        req = self.factory.get("/", {"format": "json", "callback": "callback"})
        resp = jsonified_fun(req)
        eq_(req.IS_JSON, True)
        eq_(req.CONTENT_TYPE, "application/x-javascript")
        eq_(resp.status_code, 200)


def test_template_json():
    eq_(template_json([]), '[]')
    eq_(type(template_json([])), str)
