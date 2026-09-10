from django.test.utils import override_settings
from waffle.testutils import override_switch

from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory

CHAT_WIDGET_KEY = "test-widget-key"
SNIPPET_MARKER = "static.zdassets.com/ekr/snippet.js"


@override_switch("zendesk-chat", active=True)
@override_settings(
    ZENDESK_CHAT_WIDGET_KEY=CHAT_WIDGET_KEY,
    ZENDESK_CHAT_PRODUCT_SLUGS=["firefox"],
    ZENDESK_CHAT_ELIGIBILITY_PRODUCT_SLUG="firefox-enterprise",
    ZENDESK_CHAT_LOCALES={"en-US": "en-US", "de": "de"},
)
class ChatWidgetTemplateTests(TestCase):
    """The widget snippet and its inline settings render into the page."""

    def setUp(self):
        self.user = UserFactory()
        self.product = ProductFactory(slug="firefox")

    def _get(self, locale=None):
        url = reverse("products.product", args=[self.product.slug], locale=locale)
        return self.client.get(url, follow=True)

    def test_snippet_renders_for_a_signed_in_user(self):
        self.client.force_login(self.user)
        response = self._get()

        self.assertEqual(200, response.status_code)
        self.assertContains(response, SNIPPET_MARKER)
        self.assertContains(response, CHAT_WIDGET_KEY)

    def test_token_url_is_reversed_into_the_page(self):
        """base.html renders on every page, so a missing route would 500 the site."""
        self.client.force_login(self.user)
        response = self._get()

        self.assertContains(response, "/support-chat/jwt/firefox-enterprise")

    def test_locale_is_set_to_the_page_locale(self):
        self.client.force_login(self.user)

        self.assertContains(self._get(), "'locale', 'en-US')")
        self.assertContains(self._get(locale="de"), "'locale', 'de')")

    def test_no_snippet_in_an_unmapped_locale(self):
        self.client.force_login(self.user)

        self.assertNotContains(self._get(locale="fr"), SNIPPET_MARKER)

    def test_no_snippet_for_anonymous_users(self):
        self.assertNotContains(self._get(), SNIPPET_MARKER)

    @override_switch("zendesk-chat", active=False)
    def test_no_snippet_when_the_switch_is_off(self):
        self.client.force_login(self.user)

        self.assertNotContains(self._get(), SNIPPET_MARKER)
