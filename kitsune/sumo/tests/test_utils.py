# -*- coding: utf8 -*-
import json
from unittest.mock import Mock
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test.client import RequestFactory
from nose.tools import eq_
from parameterized import parameterized

from kitsune.journal.models import Record
from kitsune.sumo.tests import TestCase
from kitsune.sumo.utils import chunked
from kitsune.sumo.utils import get_browser
from kitsune.sumo.utils import get_next_url
from kitsune.sumo.utils import has_blocked_link
from kitsune.sumo.utils import is_ratelimited
from kitsune.sumo.utils import smart_int
from kitsune.sumo.utils import truncated_json_dumps
from kitsune.users.tests import UserFactory


class SmartIntTestCase(TestCase):
    def test_sanity(self):
        eq_(10, smart_int("10"))
        eq_(10, smart_int("10.5"))

    def test_int(self):
        eq_(10, smart_int(10))

    def test_invalid_string(self):
        eq_(0, smart_int("invalid"))

    def test_empty_string(self):
        eq_(0, smart_int(""))

    def test_wrong_type(self):
        eq_(0, smart_int(None))
        eq_(10, smart_int([], 10))

    def test_large_values(self):
        """Makes sure ints that would cause an overflow result in fallback."""
        eq_(0, smart_int("1" * 1000))


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
        eq_("/new?f=b", get_next_url(r))

    def test_good_host_https(self):
        """Full URLs work with valid hosts."""
        r = self.r.post("/users/login", {"next": "https://su.mo.com/kb/new"})
        eq_("https://su.mo.com/kb/new", get_next_url(r))

    def test_post(self):
        """'next' in POST overrides GET."""
        r = self.r.post("/?next=/foo", {"next": "/bar"})
        eq_("/bar", get_next_url(r))

    def test_get(self):
        """'next' can be a query-string parameter."""
        r = self.r.get("/users/login", {"next": "/kb/new"})
        eq_("/kb/new", get_next_url(r))

    def test_referer(self):
        """Use HTTP referer if nothing else."""
        r = self.r.get("/")
        r.META["HTTP_REFERER"] = "http://su.mo.com/new"
        eq_("http://su.mo.com/new", get_next_url(r))

    def test_bad_host_https(self):
        r = self.r.get("/", {"next": "https://example.com"})
        eq_(None, get_next_url(r))

    def test_bad_host_https_debug(self):
        """If settings.DEBUG == True, bad hosts pass."""
        r = self.r.get("/", {"next": "https://example.com"})
        with self.settings(DEBUG=True):
            eq_("https://example.com", get_next_url(r))

    def test_bad_host_protocol_relative(self):
        """Protocol-relative URLs do not let bad hosts through."""
        r = self.r.get("/", {"next": "//example.com"})
        eq_(None, get_next_url(r))


class JSONTests(TestCase):
    def test_truncated_noop(self):
        """Make sure short enough things are unmodified."""
        d = {"foo": "bar"}
        trunc = truncated_json_dumps(d, 1000, "foo")
        eq_(json.dumps(d), trunc)

    def test_truncated_key(self):
        """Make sure truncation works as expected."""
        d = {"foo": "a long string that should be truncated"}
        trunc = truncated_json_dumps(d, 30, "foo")
        obj = json.loads(trunc)
        eq_(obj["foo"], "a long string that ")
        eq_(len(trunc), 30)

    def test_unicode(self):
        """Unicode should not be treated as longer than it is."""
        d = {"formula": "A=πr²"}
        trunc = truncated_json_dumps(d, 25, "formula")
        eq_(json.dumps(d, ensure_ascii=False), trunc)


class ChunkedTests(TestCase):
    def test_chunked(self):
        # chunking nothing yields nothing.
        eq_(list(chunked([], 1)), [])

        # chunking list where len(list) < n
        eq_(list(chunked([1], 10)), [[1]])

        # chunking a list where len(list) == n
        eq_(list(chunked([1, 2], 2)), [[1, 2]])

        # chunking list where len(list) > n
        eq_(list(chunked([1, 2, 3, 4, 5], 2)), [[1, 2], [3, 4], [5]])

        # passing in a length overrides the real len(list)
        eq_(list(chunked([1, 2, 3, 4, 5, 6, 7], 2, length=4)), [[1, 2], [3, 4]])


class IsRatelimitedTest(TestCase):
    def test_ratelimited(self):
        u = UserFactory()
        request = Mock()
        request.user = u
        request.limited = False
        request.method = "POST"

        # One call to the rate limit won't trigger it.
        eq_(is_ratelimited(request, "test-ratelimited", "1/min"), False)
        # But two will
        eq_(is_ratelimited(request, "test-ratelimited", "1/min"), True)

    def test_ratelimit_bypass(self):
        u = UserFactory()
        bypass = Permission.objects.get(codename="bypass_ratelimit")
        u.user_permissions.add(bypass)
        request = Mock()
        request.user = u
        request.limited = False
        request.method = "POST"

        # One call to the rate limit won't trigger it.
        eq_(is_ratelimited(request, "test-ratelimited", "1/min"), False)
        # And a second one still won't, because the user has the bypass permission.
        eq_(is_ratelimited(request, "test-ratelimited", "1/min"), False)

    def test_ratelimit_logging(self):
        u = UserFactory()
        request = Mock()
        request.user = u
        request.limited = False
        request.method = "POST"

        eq_(Record.objects.count(), 0)

        # Two calls will trigger the ratelimit once.
        is_ratelimited(request, "test-ratelimited", "1/min")
        is_ratelimited(request, "test-ratelimited", "1/min")

        eq_(Record.objects.count(), 1)


class GetBrowserNameTest(TestCase):
    def test_firefox(self):
        """Test with User Agent of Firefox"""

        user_agent = "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0"
        # Check Firefox is returning
        eq_(get_browser(user_agent), "Firefox")

    def test_chrome(self):
        """Test with User Agent of Chrome"""

        user_agent = (
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/41.0.2228.0 Safari/537.36"
        )
        # Check Chrome is returning
        eq_(get_browser(user_agent), "Chrome")

    def test_internet_explorer(self):
        """Test with User Agent of Internet Explorer"""

        # Check with default User Agent of IE 11
        user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko"
        eq_(get_browser(user_agent), "Trident")
        # Check with Compatibility View situation user Agent of IE11
        user_agent = (
            "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; "
            "Trident/7.0;  rv:11.0) like Gecko"
        )
        eq_(get_browser(user_agent), "MSIE")

    def test_safari(self):
        """Test with User Agent of Safari"""

        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14"
            "(KHTML, like Gecko) Version/7.0.3 Safari/7046A194A"
        )
        # Check Safari is returning
        eq_(get_browser(user_agent), "Safari")


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
