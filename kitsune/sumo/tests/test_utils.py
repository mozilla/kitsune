import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import Permission
from django.test.client import RequestFactory
from django.test.utils import override_settings
from parameterized import parameterized

from kitsune.journal.models import Record
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory, QuestionLocaleFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.utils import (
    get_aaq_context,
    get_aaq_url,
    get_browser,
    get_next_url,
    has_blocked_link,
    is_ratelimited,
    set_aaq_context,
    smart_int,
    truncated_json_dumps,
    webpack_static,
)
from kitsune.users.tests import UserFactory


class SmartIntTestCase(TestCase):
    def test_smart_int(self):
        for value, default, expected in (
            ("10", 0, 10),
            ("10.5", 0, 10),
            (10, 0, 10),
            ("invalid", 0, 0),
            ("", 0, 0),
            (None, 0, 0),
            ([], 10, 10),
            # Ints that would cause an overflow fall back to the default.
            ("1" * 1000, 0, 0),
        ):
            with self.subTest(value=value):
                self.assertEqual(expected, smart_int(value, default))


class GetNextUrlTests(TestCase):
    def setUp(self):
        super().setUp()
        self.r = RequestFactory()
        self.patcher = patch("django.contrib.sites.models.Site.objects")
        mock = self.patcher.start()
        mock.get_current.return_value.domain = "su.mo.com"

    def tearDown(self):
        self.patcher.stop()
        super().tearDown()

    def test_next_url(self):
        referred = self.r.get("/")
        referred.META["HTTP_REFERER"] = "http://su.mo.com/new"
        for name, request, expected in (
            ("query string kept", self.r.get("/", {"next": "/new?f=b"}), "/new?f=b"),
            (
                "full URL on a valid host",
                self.r.post("/users/login", {"next": "https://su.mo.com/kb/new"}),
                "https://su.mo.com/kb/new",
            ),
            ("POST overrides GET", self.r.post("/?next=/foo", {"next": "/bar"}), "/bar"),
            ("query-string parameter", self.r.get("/users/login", {"next": "/kb/new"}), "/kb/new"),
            ("referer when nothing else", referred, "http://su.mo.com/new"),
            ("bad host", self.r.get("/", {"next": "https://example.com"}), None),
            ("protocol-relative bad host", self.r.get("/", {"next": "//example.com"}), None),
            ("empty", self.r.get("/", {"next": ""}), None),
            ("spaces", self.r.get("/", {"next": "/kb/abc abc abc"}), "/kb/abc%20abc%20abc"),
            ("newline XSS", self.r.get("/", {"next": "j\navascrip\nt:alert()//"}), None),
            ("carriage-return XSS", self.r.get("/", {"next": "j\ravascrip\rt:alert()//"}), None),
            ("tab XSS", self.r.get("/", {"next": "j\tavascrip\tt:alert()//"}), None),
        ):
            with self.subTest(name):
                self.assertEqual(expected, get_next_url(request))

    def test_bad_host_https_debug(self):
        """If settings.DEBUG == True, bad hosts pass."""
        r = self.r.get("/", {"next": "https://example.com"})
        with self.settings(DEBUG=True):
            self.assertEqual("https://example.com", get_next_url(r))


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
        bypass, _ = Permission.objects.get_or_create(codename="bypass_ratelimit")
        u.user_permissions.add(bypass)
        request = Mock()
        request.user = u
        request.limited = False
        request.method = "POST"

        # One call to the rate limit won't trigger it.
        self.assertEqual(is_ratelimited(request, "test-ratelimited", "1/min"), False)
        # And a second one still won't, because the user has the bypass permission.
        self.assertEqual(is_ratelimited(request, "test-ratelimited", "1/min"), False)


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
            "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0;  rv:11.0) like Gecko"
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


class AAQContextTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.user = UserFactory()
        self.request = RequestFactory().get("/")
        self.request.user = self.user
        self.request.LANGUAGE_CODE = "en-US"
        self.request.session = {}

    def test_channel_context_and_locale_fallback(self):
        ProductSupportConfigFactory(
            product=self.product,
            forum_config=AAQConfigFactory(enabled_locales=[QuestionLocaleFactory(locale="en-US")]),
            zendesk_config=ZendeskConfigFactory(),
            default_support_type=ProductSupportConfig.SUPPORT_TYPE_FORUM,
        )
        expected = {
            "product_slug": self.product.slug,
            "multiple_products": True,
            "has_public_forum": True,
            "current_support_type": ProductSupportConfig.SUPPORT_TYPE_FORUM,
            "can_switch": True,
        }
        self.assertEqual(
            get_aaq_context(self.request, self.product, multiple_products=True), expected
        )

        self.request.LANGUAGE_CODE = "fr"
        expected.update(has_public_forum=False, has_default_public_forum=True)
        self.assertEqual(
            set_aaq_context(self.request, self.product, multiple_products=True), expected
        )
        self.assertEqual(self.request.session["aaq_context"], expected)

    def test_configs_without_a_usable_channel_offer_no_context(self):
        for config in (
            {"zendesk_config": ZendeskConfigFactory(), "is_active": False},
            {"forum_config": AAQConfigFactory(), "subscription_only": True},
        ):
            with self.subTest(config=config):
                product = ProductFactory()
                ProductSupportConfigFactory(product=product, **config)
                self.assertEqual(get_aaq_context(self.request, product), {})

    def test_subscription_gate_returns_only_gate_context(self):
        config = ProductSupportConfigFactory(
            product=self.product,
            zendesk_config=ZendeskConfigFactory(),
            subscription_only=True,
        )
        for redirect in (None, ProductFactory(slug="subscription-help")):
            with self.subTest(redirect=redirect):
                config.unsubscribed_redirect_product = redirect
                config.save()
                request = RequestFactory().get("/")
                request.user = self.user
                if redirect:
                    expected = {
                        "current_support_type": ProductSupportConfig.SUPPORT_TYPE_REDIRECT,
                        "redirect_url": "/en-US/questions/new/subscription-help",
                    }
                    self.assertEqual(get_aaq_url(expected), expected["redirect_url"])
                else:
                    expected = {"current_support_type": ProductSupportConfig.SUPPORT_TYPE_HIDE}
                self.assertEqual(get_aaq_context(request, self.product), expected)


class GetAAQUrlTests(TestCase):
    def test_aaq_url(self):
        single = {"has_public_forum": False, "multiple_products": False, "product_slug": "firefox"}
        for name, context, topic, expected in (
            ("empty context", {}, None, "/en-US/kb/get-community-support?exit_aaq=1"),
            (
                "ticketed single product",
                {**single, "current_support_type": "zendesk"},
                None,
                "/en-US/questions/new/firefox/form",
            ),
            (
                "forum single product",
                {**single, "current_support_type": "forum", "has_public_forum": True},
                None,
                "/en-US/questions/new/firefox/form",
            ),
            (
                "multiple products",
                {**single, "current_support_type": "zendesk", "multiple_products": True},
                None,
                "/en-US/questions/new",
            ),
            (
                "no channels, no topic",
                {**single, "current_support_type": "forum"},
                None,
                "/en-US/kb/get-community-support?exit_aaq=1",
            ),
            (
                "no channels, with topic",
                {**single, "current_support_type": "forum"},
                "some-topic",
                "/en-US/questions/new/firefox/form",
            ),
        ):
            with self.subTest(name):
                self.assertEqual(expected, get_aaq_url(context, topic=topic))
