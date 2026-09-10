from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from waffle.testutils import override_switch

from kitsune.customercare.templatetags.jinja_helpers import chat_is_available
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory

CHAT_PRODUCT_SLUGS = ["firefox", "ios", "mobile", "firefox-enterprise"]
CHAT_LOCALES = {"en-US": "en-US", "de": "de"}


@override_switch("zendesk-chat", active=True)
@override_settings(
    ZENDESK_CHAT_WIDGET_KEY="test-widget-key",
    ZENDESK_CHAT_PRODUCT_SLUGS=CHAT_PRODUCT_SLUGS,
    ZENDESK_CHAT_LOCALES=CHAT_LOCALES,
)
class ChatIsAvailableTests(TestCase):
    """Tests for the gate deciding which pages get the chat widget."""

    def setUp(self):
        self.user = UserFactory()
        self.firefox = ProductFactory(slug="firefox")
        self.thunderbird = ProductFactory(slug="thunderbird")

    def _request(self, user=None, locale="en-US"):
        return SimpleNamespace(user=user or self.user, LANGUAGE_CODE=locale)

    def test_page_about_a_chat_product(self):
        self.assertTrue(chat_is_available(self._request(), [self.firefox]))

    def test_page_about_another_product(self):
        self.assertFalse(chat_is_available(self._request(), [self.thunderbird]))

    def test_one_chat_product_is_enough(self):
        """A KB article can belong to several products."""
        self.assertTrue(chat_is_available(self._request(), [self.thunderbird, self.firefox]))

    def test_page_about_no_product_skips_the_product_check(self):
        """The home page isn't about a product, but still gets chat."""
        self.assertTrue(chat_is_available(self._request()))

    def test_empty_product_list_is_not_the_same_as_omitting_it(self):
        self.assertFalse(chat_is_available(self._request(), []))

    def test_translated_page_in_a_supported_locale(self):
        self.assertTrue(chat_is_available(self._request(locale="de"), [self.firefox]))

    def test_translated_page_in_an_unsupported_locale(self):
        """Zendesk ignores a locale it doesn't know, so we hide chat rather than
        let the widget fall back to the browser's language."""
        self.assertFalse(chat_is_available(self._request(locale="fr"), [self.firefox]))

    def test_anonymous_user(self):
        self.assertFalse(chat_is_available(self._request(user=AnonymousUser()), [self.firefox]))

    @override_switch("zendesk-chat", active=False)
    def test_switch_off(self):
        self.assertFalse(chat_is_available(self._request(), [self.firefox]))

    @override_settings(ZENDESK_CHAT_WIDGET_KEY="")
    def test_no_widget_key_configured(self):
        self.assertFalse(chat_is_available(self._request(), [self.firefox]))
