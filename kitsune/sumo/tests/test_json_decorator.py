import json

from django import http
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from kitsune.sumo.decorators import json_view

rf = RequestFactory()
JSON = "application/json"


class JsonViewTests(TestCase):
    def test_object(self):
        data = {
            "foo": "bar",
            "baz": "qux",
            "quz": [{"foo": "bar"}],
        }
        expect = json.dumps(data).encode()

        @json_view
        def temp(req):
            return data

        res = temp(rf.get("/"))
        self.assertEqual(200, res.status_code)
        self.assertEqual(expect, res.content)
        self.assertEqual(JSON, res["content-type"])

    def test_list(self):
        data = ["foo", "bar", "baz"]
        expect = json.dumps(data).encode()

        @json_view
        def temp(req):
            return data

        res = temp(rf.get("/"))
        self.assertEqual(200, res.status_code)
        self.assertEqual(expect, res.content)
        self.assertEqual(JSON, res["content-type"])

    def test_404(self):
        @json_view
        def temp(req):
            raise http.Http404("foo")

        res = temp(rf.get("/"))
        self.assertEqual(404, res.status_code)
        self.assertEqual(JSON, res["content-type"])
        data = json.loads(res.content)
        self.assertEqual(404, data["error"])
        self.assertEqual("foo", data["message"])

    def test_permission(self):
        @json_view
        def temp(req):
            raise PermissionDenied("bar")

        res = temp(rf.get("/"))
        self.assertEqual(403, res.status_code)
        self.assertEqual(JSON, res["content-type"])
        data = json.loads(res.content)
        self.assertEqual(403, data["error"])
        self.assertEqual("bar", data["message"])

    def test_server_error(self):
        @json_view
        def temp(req):
            raise TypeError("fail")

        res = temp(rf.get("/"))
        self.assertEqual(500, res.status_code)
        self.assertEqual(JSON, res["content-type"])
        data = json.loads(res.content)
        self.assertEqual(500, data["error"])
        self.assertEqual("fail", data["message"])
