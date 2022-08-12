from django.http import HttpResponse
from django.test.client import RequestFactory

from kitsune.sumo.json_utils import jsonp_is_valid, markup_json, template_json
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
        TestCase().assertEqual(jsonp_is_valid(funcname), expected)


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
        self.assertEqual(req.IS_JSON, False)
        self.assertEqual(resp.status_code, 200)

    def test_is_json_false_wrong_format(self):
        req = self.factory.get("/", {"format": "html"})
        resp = jsonified_fun(req)
        self.assertEqual(req.IS_JSON, False)
        self.assertEqual(resp.status_code, 200)

    def test_is_json_true(self):
        req = self.factory.get("/", {"format": "json"})
        resp = jsonified_fun(req)
        self.assertEqual(req.IS_JSON, True)
        self.assertEqual(resp.status_code, 200)

    def test_json_callback_not_is_json(self):
        req = self.factory.get("/")
        resp = jsonified_fun(req)
        self.assertEqual(req.IS_JSON, False)
        self.assertEqual(req.JSON_CALLBACK, "")
        self.assertEqual(resp.status_code, 200)

    def test_json_callback_valid(self):
        req = self.factory.get("/", {"format": "json", "callback": "callback"})
        resp = jsonified_fun(req)
        self.assertEqual(req.IS_JSON, True)
        self.assertEqual(req.JSON_CALLBACK, "callback")
        self.assertEqual(resp.status_code, 200)

    def test_json_callback_invalid(self):
        req = self.factory.get("/", {"format": "json", "callback": '">'})
        resp = jsonified_fun(req)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content, b'{"error": "Invalid callback function."}')

    def test_content_type_not_json(self):
        req = self.factory.get("/")
        resp = jsonified_fun(req)
        self.assertEqual(req.IS_JSON, False)
        self.assertEqual(req.CONTENT_TYPE, "text/html")
        self.assertEqual(resp.status_code, 200)

    def test_content_type_json(self):
        req = self.factory.get("/", {"format": "json"})
        resp = jsonified_fun(req)
        self.assertEqual(req.IS_JSON, True)
        self.assertEqual(req.CONTENT_TYPE, "application/json")
        self.assertEqual(resp.status_code, 200)

    def test_content_type_jsonp(self):
        req = self.factory.get("/", {"format": "json", "callback": "callback"})
        resp = jsonified_fun(req)
        self.assertEqual(req.IS_JSON, True)
        self.assertEqual(req.CONTENT_TYPE, "application/x-javascript")
        self.assertEqual(resp.status_code, 200)


def test_template_json():
    tc = TestCase()
    tc.assertEqual(template_json([]), "[]")
    tc.assertEqual(type(template_json([])), str)
