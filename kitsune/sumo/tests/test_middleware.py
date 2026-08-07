from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.test import override_settings
from django.test.client import RequestFactory

from kitsune.sumo.checks import (
    NUL_STRIPPING_MIDDLEWARE,
    check_nul_stripping_middleware,
    nul_stripping_middleware_problems,
)
from kitsune.sumo.middleware import (
    CacheHeadersMiddleware,
    EnforceHostIPMiddleware,
    GeoIPCookieMiddleware,
    PlusToSpaceMiddleware,
    SetRemoteAddr,
    StripNulCharactersMiddleware,
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


class SetRemoteAddrFromForwardedForMiddlewareTestCase(TestCase):
    def test_when_no_trusted_proxies(self):
        with self.settings(TRUSTED_PROXY_COUNT=0), self.assertRaises(MiddlewareNotUsed):
            SetRemoteAddr(lambda *args, **kwargs: HttpResponse())

    def test_when_one_or_more_trusted_proxies(self):
        rf = RequestFactory()
        mw = SetRemoteAddr(lambda *args, **kwargs: HttpResponse())
        for fastly_client_ip, proxy_count, forwarded_for, expected in [
            (None, 1, " ", "127.0.0.1"),
            (None, 1, "1.1.1.1", "127.0.0.1"),
            (None, 1, "684D:1:2:3:4:55:6:7", "127.0.0.1"),
            (None, 1, "1.1.1.1, 2.2.2.2", "1.1.1.1"),
            (None, 1, "684D:1:2:3:4:55:6:7, 2001:DB8::FF00:42:8329", "684d:1:2:3:4:55:6:7"),
            (
                None,
                1,
                "3.3.3.3, 2001:DB8::FF00:42:8329, 684D:1:2:3:4:55:6:7",
                "2001:db8::ff00:42:8329",
            ),
            (None, 1, " yädâ , yädâ.ÿådá.😜.🤪 , yädâ", "127.0.0.1"),
            (None, 1, " yädâ , yädâ, ,1.1.1.1, 2.2.2.2", "1.1.1.1"),
            (None, 2, "3.3.3.3", "127.0.0.1"),
            (None, 2, "2.2.2.2,  3.3.3.3,  4.4.4.4", "2.2.2.2"),
            (None, 2, "3.3.3.3, 4.4.4.4,5.5.5.5", "3.3.3.3"),
            (None, 2, "999.255.255.1, 4.4.4.4,5.5.5.5", "127.0.0.1"),
            (None, 2, None, "127.0.0.1"),
            ("3.3.3.3", 1, "1.1.1.1, 2.2.2.2", "3.3.3.3"),
            (
                "684D:1:2:3:4:55:6:5",
                1,
                "684D:1:2:3:4:55:6:7, 2001:DB8::FF00:42:8329",
                "684d:1:2:3:4:55:6:5",
            ),
            (
                "2001:DB8::FF00:42:8327",
                1,
                "3.3.3.3, 2001:DB8::FF00:42:8329, 684D:1:2:3:4:55:6:7",
                "2001:db8::ff00:42:8327",
            ),
            ("4.4.4.4", 1, " yädâ , yädâ.ÿådá.😜.🤪 , yädâ", "4.4.4.4"),
            ("yädâ", 1, " yädâ , yädâ.ÿådá.😜.🤪 , yädâ", "127.0.0.1"),
            ("yädâ", 1, None, "127.0.0.1"),
            ("yädâ", 1, " yädâ , yädâ, ,1.1.1.1, 2.2.2.2", "1.1.1.1"),
            ("4.4.4.4", 2, "3.3.3.3", "4.4.4.4"),
            ("5.5.5.5", 2, "2.2.2.2,  3.3.3.3,  4.4.4.4", "5.5.5.5"),
            ("yädâ", 2, "3.3.3.3, 4.4.4.4,5.5.5.5", "3.3.3.3"),
            ("yädâ", 2, "999.255.255.1, 4.4.4.4,5.5.5.5", "127.0.0.1"),
        ]:
            with (
                self.settings(TRUSTED_PROXY_COUNT=proxy_count),
                self.subTest(f"{fastly_client_ip} with {proxy_count} and {forwarded_for}"),
            ):
                kwargs = {}
                if forwarded_for:
                    kwargs["HTTP_X_FORWARDED_FOR"] = forwarded_for
                if fastly_client_ip:
                    kwargs["HTTP_FASTLY_CLIENT_IP"] = fastly_client_ip
                request = rf.get("/", **kwargs)
                mw(request)
                self.assertEqual(request.META["REMOTE_ADDR"], expected)


class GeoIPCookieMiddlewareTestCase(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.mw = GeoIPCookieMiddleware(lambda r: HttpResponse())

    def test_header_sets_cookie(self):
        request = self.rf.get(
            "/",
            HTTP_X_CLIENT_GEO_COUNTRY_NAME="United States",
        )
        response = HttpResponse()
        response = self.mw.process_response(request, response)
        self.assertEqual(response.cookies["geoip_country_name"].value, "United States")

    def test_no_header_sets_no_cookie(self):
        request = self.rf.get("/")
        response = HttpResponse()
        response = self.mw.process_response(request, response)
        self.assertNotIn("geoip_country_name", response.cookies)


class StripNulCharactersMiddlewareTestCase(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.mw = StripNulCharactersMiddleware(lambda r: HttpResponse())

    def test_percent_encoded_nul_is_stripped(self):
        request = self.rf.get("/questions/?tagged=%00abc&page=2")
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "abc")
        self.assertEqual(request.GET["page"], "2")

    def test_raw_nul_is_stripped(self):
        """A NUL can arrive unencoded rather than as %00."""
        request = self.rf.get("/questions/")
        request.META["QUERY_STRING"] = "tagged=a\x00b"
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "ab")

    def test_repeated_nul_is_stripped(self):
        request = self.rf.get("/questions/?tagged=%00%00a%00b")
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "ab")

    def test_doubled_percent_nul_is_stripped(self):
        """The first "%" is literal, so the text "%00" is left behind, not a NUL."""
        request = self.rf.get("/questions/?tagged=%%0000abc")
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "%00abc")
        self.assertNotIn("\x00", request.GET["tagged"])

    def test_raw_nul_inside_an_escape_is_stripped(self):
        """Dropping the raw NUL must not leave the "%" reading as an escape."""
        request = self.rf.get("/questions/")
        request.META["QUERY_STRING"] = "tagged=%\x0000abc"
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "%00abc")
        self.assertNotIn("\x00", request.GET["tagged"])

    def test_multi_value_parameters_are_preserved(self):
        request = self.rf.get("/questions/?product=%00firefox&product=thunderbird%00")
        self.mw.process_request(request)
        self.assertEqual(request.GET.getlist("product"), ["firefox", "thunderbird"])

    def test_nul_in_parameter_name_is_stripped(self):
        request = self.rf.get("/questions/?tag%00ged=abc")
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "abc")

    def test_get_full_path_is_cleaned(self):
        """Redirect targets and logs are built from get_full_path()."""
        request = self.rf.get("/questions/?tagged=%00abc")
        self.mw.process_request(request)
        self.assertEqual(request.get_full_path(), "/questions/?tagged=abc")

    def test_clean_query_string_is_left_alone(self):
        request = self.rf.get("/questions/?tagged=abc&page=2")
        self.mw.process_request(request)
        self.assertEqual(request.META["QUERY_STRING"], "tagged=abc&page=2")

    def test_missing_query_string(self):
        """QUERY_STRING may be absent from the WSGI environ."""
        request = self.rf.get("/questions/")
        del request.META["QUERY_STRING"]
        self.mw.process_request(request)
        self.assertNotIn("QUERY_STRING", request.META)
        self.assertEqual(dict(request.GET), {})

    def test_double_encoded_nul_is_preserved(self):
        """%2500 is a literal "%00" in the value, not a NUL, so it must survive."""
        request = self.rf.get("/questions/?tagged=%2500")
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "%00")

    def test_non_ascii_values_are_preserved(self):
        request = self.rf.get("/questions/?q=caf%C3%A9%00")
        self.mw.process_request(request)
        self.assertEqual(request.GET["q"], "café")

    def test_raw_non_ascii_query_string_is_preserved(self):
        """The WSGI environ carries the query string as latin-1."""
        request = self.rf.get("/questions/")
        request.META["QUERY_STRING"] = "q=café\x00".encode().decode("iso-8859-1")
        self.mw.process_request(request)
        self.assertEqual(request.GET["q"], "café")

    def test_survives_encoding_reassignment(self):
        """Setting request.encoding discards the parsed GET, so it must re-parse clean."""
        request = self.rf.get("/questions/?tagged=%00abc")
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "abc")
        request.encoding = "utf-8"
        self.assertEqual(request.GET["tagged"], "abc")

    def test_already_parsed_get_is_not_relied_upon(self):
        """Cleaning QUERY_STRING cannot fix a GET that was parsed before we ran,
        which is why the ordering in settings.MIDDLEWARE matters."""
        request = self.rf.get("/questions/?tagged=%00abc")
        self.assertEqual(request.GET["tagged"], "\x00abc")
        self.mw.process_request(request)
        self.assertEqual(request.GET["tagged"], "\x00abc")


class StripNulCharactersRequestTestCase(TestCase):
    """The unit tests above call the middleware directly. These go through the
    real MIDDLEWARE, so they also cover it being wired in early enough."""

    def test_nul_in_a_filter_that_reaches_postgres(self):
        """?tagged= is looked up with slug__in. Drop the middleware and this 500s."""
        response = self.client.get("/en-US/questions/all", {"tagged": "\x00support"})
        self.assertEqual(response.status_code, 200)

    def test_doubled_percent_nul_in_a_filter(self):
        """The malformed spelling has to survive the whole stack too."""
        response = self.client.get("/en-US/questions/all?tagged=%%0000support")
        self.assertEqual(response.status_code, 200)


class NulStrippingOrderCheckTestCase(TestCase):
    """The check is what guards the ordering, so these test the check itself."""

    OTHER_MIDDLEWARE = "acme.middleware.SomeMiddleware"

    def test_the_real_middleware_is_ordered_correctly(self):
        self.assertEqual(nul_stripping_middleware_problems(), [])

    def test_anything_in_front_is_reported(self):
        with override_settings(MIDDLEWARE=(self.OTHER_MIDDLEWARE, *settings.MIDDLEWARE)):
            problems = nul_stripping_middleware_problems()
        self.assertEqual(len(problems), 1)
        self.assertIn("must be the first entry", problems[0])

    def test_anything_behind_is_left_alone(self):
        with override_settings(MIDDLEWARE=(*settings.MIDDLEWARE, self.OTHER_MIDDLEWARE)):
            self.assertEqual(nul_stripping_middleware_problems(), [])

    def test_middleware_missing_altogether_is_reported(self):
        without = tuple(m for m in settings.MIDDLEWARE if m != NUL_STRIPPING_MIDDLEWARE)
        with override_settings(MIDDLEWARE=without):
            self.assertEqual(len(nul_stripping_middleware_problems()), 1)

    def test_empty_middleware_is_reported(self):
        """Nothing may index into an empty MIDDLEWARE and blow up."""
        with override_settings(MIDDLEWARE=()):
            self.assertEqual(len(nul_stripping_middleware_problems()), 1)

    def test_problems_are_raised_as_errors(self):
        with override_settings(MIDDLEWARE=(self.OTHER_MIDDLEWARE, *settings.MIDDLEWARE)):
            errors = check_nul_stripping_middleware(app_configs=None)
        self.assertEqual([error.id for error in errors], ["sumo.E001"])
