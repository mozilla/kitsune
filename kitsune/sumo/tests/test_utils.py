# -*- coding: utf8 -*-
import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import Permission
from django.test.client import RequestFactory
from django.test.utils import override_settings
from parameterized import parameterized

from kitsune.journal.models import Record
from kitsune.sumo.tests import TestCase
from kitsune.sumo.utils import (
    chunked,
    get_browser,
    get_next_url,
    has_blocked_link,
    is_ratelimited,
    smart_int,
    truncated_json_dumps,
    webpack_static,
)
from kitsune.users.tests import UserFactory


class SmartIntTestCase(TestCase):
    def test_sanity(self):
        self.assertEqual(10, smart_int("10"))
        self.assertEqual(10, smart_int("10.5"))

    def test_int(self):
        self.assertEqual(10, smart_int(10))

    def test_invalid_string(self):
        self.assertEqual(0, smart_int("invalid"))

    def test_empty_string(self):
        self.assertEqual(0, smart_int(""))

    def test_wrong_type(self):
        self.assertEqual(0, smart_int(None))
        self.assertEqual(10, smart_int([], 10))

    def test_large_values(self):
        """Makes sure ints that would cause an overflow result in fallback."""
        self.assertEqual(0, smart_int("1" * 1000))


class GetNextUrlTests(TestCase):
    def setUp(self):
        super(GetNextUrlTests, self).setUp()
        self.r = RequestFactory()
        self.patcher = patch("django.contrib.sites.models.Site.objects")
        mock = self.patcher.start()
        mock.get_current.return_value.domain = "su.mo.com"

    def tearDown(self):
        self.patcher.stop()
        super(GetNextUrlTests, self).tearDown()

    def test_query_string(self):
        """Query-strings remain intact."""
        r = self.r.get("/", {"next": "/new?f=b"})
        self.assertEqual("/new?f=b", get_next_url(r))

    def test_good_host_https(self):
        """Full URLs work with valid hosts."""
        r = self.r.post("/users/login", {"next": "https://su.mo.com/kb/new"})
        self.assertEqual("https://su.mo.com/kb/new", get_next_url(r))

    def test_post(self):
        """'next' in POST overrides GET."""
        r = self.r.post("/?next=/foo", {"next": "/bar"})
        self.assertEqual("/bar", get_next_url(r))

    def test_get(self):
        """'next' can be a query-string parameter."""
        r = self.r.get("/users/login", {"next": "/kb/new"})
        self.assertEqual("/kb/new", get_next_url(r))

    def test_referer(self):
        """Use HTTP referer if nothing else."""
        r = self.r.get("/")
        r.META["HTTP_REFERER"] = "http://su.mo.com/new"
        self.assertEqual("http://su.mo.com/new", get_next_url(r))

    def test_bad_host_https(self):
        r = self.r.get("/", {"next": "https://example.com"})
        self.assertEqual(None, get_next_url(r))

    def test_bad_host_https_debug(self):
        """If settings.DEBUG == True, bad hosts pass."""
        r = self.r.get("/", {"next": "https://example.com"})
        with self.settings(DEBUG=True):
            self.assertEqual("https://example.com", get_next_url(r))

    def test_bad_host_protocol_relative(self):
        """Protocol-relative URLs do not let bad hosts through."""
        r = self.r.get("/", {"next": "//example.com"})
        self.assertEqual(None, get_next_url(r))

    def test_when_empty(self):
        """Next url is empty"""
        r = self.r.get("/", {"next": ""})
        self.assertEqual(None, get_next_url(r))

    def test_when_spaces(self):
        """Next url contains one or more spaces"""
        r = self.r.get("/", {"next": "/kb/abc abc abc"})
        self.assertEqual("/kb/abc%20abc%20abc", get_next_url(r))

    def test_xss_attempt_with_newline(self):
        """Next url with newline-based xss attempt"""
        r = self.r.get("/", {"next": "j\navascrip\nt:alert()//"})
        self.assertEqual(None, get_next_url(r))

    def test_xss_attempt_with_carriage_return(self):
        """Next url with carriage-return-based xss attempt"""
        r = self.r.get("/", {"next": "j\ravascrip\rt:alert()//"})
        self.assertEqual(None, get_next_url(r))

    def test_xss_attempt_with_tab(self):
        """Next url with tab-based xss attempt"""
        r = self.r.get("/", {"next": "j\tavascrip\tt:alert()//"})
        self.assertEqual(None, get_next_url(r))


class JSONTests(TestCase):
    def test_truncated_noop(self):
        """Make sure short enough things are unmodified."""
        d = {"foo": "bar"}
        trunc = truncated_json_dumps(d, 1000, "foo")
        self.assertEqual(json.dumps(d), trunc)

    def test_truncated_key(self):
        """Make sure truncation works as expected."""
        d = {"foo": "a long string that should be truncated"}
        trunc = truncated_json_dumps(d, 30, "foo")
        obj = json.loads(trunc)
        self.assertEqual(obj["foo"], "a long string that ")
        self.assertEqual(len(trunc), 30)

    def test_unicode(self):
        """Unicode should not be treated as longer than it is."""
        d = {"formula": "A=πr²"}
        trunc = truncated_json_dumps(d, 25, "formula")
        self.assertEqual(json.dumps(d, ensure_ascii=False), trunc)


class ChunkedTests(TestCase):
    def test_chunked(self):
        # chunking nothing yields nothing.
        self.assertEqual(list(chunked([], 1)), [])

        # chunking list where len(list) < n
        self.assertEqual(list(chunked([1], 10)), [[1]])

        # chunking a list where len(list) == n
        self.assertEqual(list(chunked([1, 2], 2)), [[1, 2]])

        # chunking list where len(list) > n
        self.assertEqual(list(chunked([1, 2, 3, 4, 5], 2)), [[1, 2], [3, 4], [5]])

        # passing in a length overrides the real len(list)
        self.assertEqual(list(chunked([1, 2, 3, 4, 5, 6, 7], 2, length=4)), [[1, 2], [3, 4]])


class IsRatelimitedTest(TestCase):
    def test_ratelimited_grouping_by_name_and_rate(self):
        """Ensure that both the name and the rate differentiate the counting group."""
        request = Mock()
        request.user = UserFactory()
        request.limited = False
        request.method = "POST"

        self.assertEqual(is_ratelimited(request, "test1", "1/min"), False)
        self.assertEqual(is_ratelimited(request, "test2", "1/min"), False)
        self.assertEqual(is_ratelimited(request, "test1", "1/d"), False)
        self.assertEqual(is_ratelimited(request, "test1", "1/min"), True)

        request.limited = False
        self.assertEqual(is_ratelimited(request, "test2", "1/min"), True)

        request.limited = False
        self.assertEqual(is_ratelimited(request, "test1", "1/d"), True)

    def test_ratelimited_restriction_by_http_method(self):
        """Ensure that the HTTP method(s) is(are) respected."""
        request = Mock()
        request.user = UserFactory()
        request.limited = False

        request.method = "POST"
        self.assertEqual(is_ratelimited(request, "test3", "1/min", "GET"), False)
        self.assertEqual(is_ratelimited(request, "test3", "1/min", "GET"), False)

        request.method = "GET"
        self.assertEqual(is_ratelimited(request, "test3", "1/min", "GET"), False)
        self.assertEqual(is_ratelimited(request, "test3", "1/min", "GET"), True)

        request.limited = False
        request.method = "GET"
        self.assertEqual(is_ratelimited(request, "test3", "1/min", ("PUT", "POST")), False)
        request.method = "PUT"
        self.assertEqual(is_ratelimited(request, "test3", "1/min", ("PUT", "POST")), False)
        request.method = "POST"
        self.assertEqual(is_ratelimited(request, "test3", "1/min", ("PUT", "POST")), True)

    def test_ratelimited_when_already_limited(self):
        """
        Ensure that if the request is already limited, then it should remain
        limited, but the counting group should still be incremented when called.
        """
        request = Mock()
        request.user = UserFactory()
        request.limited = True
        request.method = "POST"

        num_records_before = Record.objects.count()
        # This call should return True since the request was already limited,
        # but it should still increment the "test4 1/min" group.
        self.assertEqual(is_ratelimited(request, "test4", "1/min"), True)
        # It should not have logged a record of the ratelimit since it
        # occurred prior to this call.
        self.assertEqual(Record.objects.count(), num_records_before)

        request.limited = False
        # Let's confirm that the previous call really did increment.
        self.assertEqual(is_ratelimited(request, "test4", "1/min"), True)
        # This time we should have logged a record since it was our own ratelimit event.
        self.assertEqual(Record.objects.count(), num_records_before + 1)

    def test_ratelimit_bypass(self):
        u = UserFactory()
        bypass = Permission.objects.get(codename="bypass_ratelimit")
        u.user_permissions.add(bypass)
        request = Mock()
        request.user = u
        request.limited = False
        request.method = "POST"

        # One call to the rate limit won't trigger it.
        self.assertEqual(is_ratelimited(request, "test-ratelimited", "1/min"), False)
        # And a second one still won't, because the user has the bypass permission.
        self.assertEqual(is_ratelimited(request, "test-ratelimited", "1/min"), False)

    def test_ratelimit_logging(self):
        u = UserFactory()
        request = Mock()
        request.user = u
        request.limited = False
        request.method = "POST"

        self.assertEqual(Record.objects.count(), 0)

        # Two calls will trigger the ratelimit once.
        is_ratelimited(request, "test-ratelimited", "1/min")
        is_ratelimited(request, "test-ratelimited", "1/min")

        self.assertEqual(Record.objects.count(), 1)


class GetBrowserNameTest(TestCase):
    def test_firefox(self):
        """Test with User Agent of Firefox"""

        user_agent = "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0"
        # Check Firefox is returning
        self.assertEqual(get_browser(user_agent), "Firefox")

    def test_chrome(self):
        """Test with User Agent of Chrome"""

        user_agent = (
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/41.0.2228.0 Safari/537.36"
        )
        # Check Chrome is returning
        self.assertEqual(get_browser(user_agent), "Chrome")

    def test_internet_explorer(self):
        """Test with User Agent of Internet Explorer"""

        # Check with default User Agent of IE 11
        user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko"
        self.assertEqual(get_browser(user_agent), "Trident")
        # Check with Compatibility View situation user Agent of IE11
        user_agent = (
            "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; "
            "Trident/7.0;  rv:11.0) like Gecko"
        )
        self.assertEqual(get_browser(user_agent), "MSIE")

    def test_safari(self):
        """Test with User Agent of Safari"""

        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14"
            "(KHTML, like Gecko) Version/7.0.3 Safari/7046A194A"
        )
        # Check Safari is returning
        self.assertEqual(get_browser(user_agent), "Safari")


class HasLinkTests(TestCase):
    @parameterized.expand(
        [
            ("test.example", False),
            ("mozilla.com", False),
            ("subdomain.mozilla.com", False),
            ("mozilla.com.mozilla.com", False),
            ("MOZILLA.COM", False),
            ("example.mozilla.com.mozilla.com", False),
            ("255.256.255.255", False),
            ("255.255.255", False),
            ("mozilla.com example.com", True),
            ("mozilla.com fakemozilla.com", True),
            ("mozilla.com mozilla.com.example.com", True),
            ("mozilla.com example.mozilla.com.example.com", True),
            ("mozilla.com punycode.XN--11B4C3D", True),
            ("mozilla.com 255.255.255.255", True),
            ("mozilla.com 0.0.0.0", True),
        ]
    )
    def test_urls(self, data, expected_result):
        result = has_blocked_link(data)
        self.assertEqual(result, expected_result)


class WebpackStaticTests(TestCase):
    @override_settings(DEBUG=False)
    def test_no_exception(self):
        webpack_static("this_file_does_not_exist")

    @override_settings(DEBUG=True)
    def test_exception(self):
        with self.assertRaises(RuntimeError):
            webpack_static("this_file_does_not_exist")
