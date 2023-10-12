from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.test import override_settings
from django.test.client import RequestFactory

from kitsune.sumo.middleware import (
    CacheHeadersMiddleware,
    EnforceHostIPMiddleware,
    PlusToSpaceMiddleware,
)
from kitsune.sumo.tests import TestCase


@override_settings(ENFORCE_HOST=["support.mozilla.org", "all-your-base.are-belong-to.us"])
class EnforceHostIPMiddlewareTestCase(TestCase):
    def g_response(*args, **kwargs):
        return HttpResponse()

    def _get_response(self, hostname):
        mw = EnforceHostIPMiddleware(self.g_response)
        rf = RequestFactory()
        return mw(rf.get("/", HTTP_HOST=hostname))

    def test_valid_domain(self):
        resp = self._get_response("support.mozilla.org")
        self.assertEqual(resp.status_code, 200)

    def test_valid_ip_address(self):
        resp = self._get_response("192.168.200.200")
        self.assertEqual(resp.status_code, 200)
        # with port
        resp = self._get_response("192.168.200.200:443")
        self.assertEqual(resp.status_code, 200)

    def test_invalid_domain(self):
        resp = self._get_response("none-of-ur-base.are-belong-to.us")
        assert isinstance(resp, HttpResponsePermanentRedirect)


class CacheHeadersMiddlewareTestCase(TestCase):
    def g_response(*args, **kwargs):
        return HttpResponse()

    def setUp(self):
        self.get_response = self.g_response()
        self.rf = RequestFactory()
        self.mw = CacheHeadersMiddleware(self.get_response)

    @override_settings(CACHE_MIDDLEWARE_SECONDS=60)
    def test_add_cache_control(self):
        req = self.rf.get("/")
        resp = HttpResponse("OK")
        resp = self.mw.process_response(req, resp)
        assert resp.headers["cache-control"] == "max-age=60"

    @override_settings(CACHE_MIDDLEWARE_SECONDS=60)
    def test_already_has_cache_control(self):
        req = self.rf.get("/")
        resp = HttpResponse("OK")
        resp.headers["cache-control"] = "no-cache"
        resp = self.mw.process_response(req, resp)
        assert resp.headers["cache-control"] == "no-cache"

    @override_settings(CACHE_MIDDLEWARE_SECONDS=60)
    def test_non_200_response(self):
        req = self.rf.get("/")
        resp = HttpResponse("WHA?", status=404)
        resp = self.mw.process_response(req, resp)
        assert "cache-control" not in resp.headers

    @override_settings(CACHE_MIDDLEWARE_SECONDS=0)
    def test_middleware_seconds_0(self):
        req = self.rf.get("/")
        resp = HttpResponse("OK")
        resp = self.mw.process_response(req, resp)
        assert (
            resp.headers["cache-control"]
            == "max-age=0, no-cache, no-store, must-revalidate, private"
        )

    @override_settings(CACHE_MIDDLEWARE_SECONDS=60)
    def test_post_request(self):
        req = self.rf.post("/")
        resp = HttpResponse("OK")
        resp = self.mw.process_response(req, resp)
        assert (
            resp.headers["cache-control"]
            == "max-age=0, no-cache, no-store, must-revalidate, private"
        )


class TrailingSlashMiddlewareTestCase(TestCase):
    def test_no_trailing_slash(self):
        response = self.client.get("/en-US/ohnoez")
        self.assertEqual(response.status_code, 404)

    def test_no_trailing_slash_without_locale_in_path(self):
        response = self.client.get("/ohnoez")
        self.assertEqual(response.status_code, 404)

    def test_404_trailing_slash(self):
        response = self.client.get("/en-US/ohnoez/")
        self.assertEqual(response.status_code, 404)

    def test_404_trailing_slash_without_locale_in_path(self):
        response = self.client.get("/ohnoez/")
        self.assertEqual(response.status_code, 404)

    def test_remove_trailing_slash(self):
        response = self.client.get("/en-US/home/?xxx=%C3%83")
        self.assertEqual(response.status_code, 301)
        assert response.headers["Location"].endswith("/en-US/home?xxx=%C3%83")

    def test_remove_trailing_slash_without_locale_in_path(self):
        response = self.client.get("/home/?xxx=%C3%83")
        self.assertEqual(response.status_code, 301)
        assert response.headers["Location"].endswith("/home?xxx=%C3%83")


class PlusToSpaceTestCase(TestCase):
    def g_response(*args, **kwargs):
        return HttpResponse()

    get_response = g_response()
    rf = RequestFactory()
    ptsm = PlusToSpaceMiddleware(get_response)

    def test_plus_to_space(self):
        """Pluses should be converted to %20."""
        request = self.rf.get("/url+with+plus")
        # should work without a QUERY_STRING key in META
        del request.META["QUERY_STRING"]
        response = self.ptsm.process_request(request)
        assert isinstance(response, HttpResponsePermanentRedirect)
        self.assertEqual("/url%20with%20plus", response.headers["location"])

    def test_query_string(self):
        """Query strings should be maintained."""
        request = self.rf.get("/pa+th", {"a": "b"})
        response = self.ptsm.process_request(request)
        self.assertEqual("/pa%20th?a=b", response.headers["location"])

    def test_query_string_unaffected(self):
        """Pluses in query strings are not affected."""
        request = self.rf.get("/pa+th?var=a+b")
        response = self.ptsm.process_request(request)
        self.assertEqual("/pa%20th?var=a+b", response.headers["location"])

    def test_pass_through(self):
        """URLs without a + should be left alone."""
        request = self.rf.get("/path")
        assert not self.ptsm.process_request(request)

    def test_with_locale(self):
        """URLs with a locale should keep it."""
        request = self.rf.get("/ru/pa+th", {"a": "b"})
        response = self.ptsm.process_request(request)
        self.assertEqual("/ru/pa%20th?a=b", response.headers["location"])

    def test_with_non_unicode_query_string(self):
        """The request QUERY_STRING might not be unicode."""
        request = self.rf.get("/ja/pa+th")
        request.META["QUERY_STRING"] = "s=%E3%82%A2"
        response = self.ptsm.process_request(request)
        self.assertEqual("/ja/pa%20th?s=%E3%82%A2", response.headers["location"])
