from django.contrib.auth.models import Group
from django.test.utils import override_settings
from waffle.testutils import override_switch

from kitsune.groups.models import GroupProfile
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    ZendeskConfigFactory,
)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.tests.test_middleware import csp_directives
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory

CHAT_WIDGET_KEY = "test-widget-key"
SNIPPET_MARKER = "static.zdassets.com/ekr/snippet.js"


@override_switch("zendesk-chat", active=True)
@override_settings(
    ZENDESK_CHAT_WIDGET_KEY=CHAT_WIDGET_KEY,
    ZENDESK_CHAT_SIGNING_SECRET="test-signing-secret",
    ZENDESK_CHAT_SIGNING_KEY_ID="test-key-id",
    ZENDESK_CHAT_SUPPORTED_NON_ENGLISH_LOCALES=["de"],
)
class ChatWidgetTemplateTests(TestCase):
    """Test that the widget snippet and its inline settings render into the page."""

    def setUp(self):
        self.product = ProductFactory(slug="firefox-enterprise")
        config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )
        root = GroupProfile.add_root(group=Group.objects.create(name="chat"), slug="chat")
        company = root.add_child(group=Group.objects.create(name="company"), slug="company")
        SupportOrganizationFactory(config=config, group=company.group, include_live_chat=True)
        self.user = UserFactory()
        self.user.groups.add(company.group)

    def _get(self, locale=None):
        url = reverse("products.product", args=[self.product.slug], locale=locale)
        return self.client.get(url, follow=True)

    def test_snippet_renders_for_an_entitled_user(self):
        self.client.force_login(self.user)
        response = self._get()

        self.assertEqual(200, response.status_code)
        self.assertContains(response, SNIPPET_MARKER)
        self.assertContains(response, CHAT_WIDGET_KEY)

    def test_the_page_carries_the_token_url_and_the_user(self):
        self.client.force_login(self.user)
        response = self._get()

        self.assertContains(response, "/support-chat/jwt/firefox-enterprise")
        self.assertContains(response, f'data-zendesk-chat-user="{self.user.id}"')

    @override_settings(ZENDESK_CHAT_TAGS="stage other")
    def test_the_page_carries_the_chat_tags_and_the_product_tag(self):
        self.client.force_login(self.user)

        self.assertContains(
            self._get(), 'data-zendesk-chat-tags="stage other product-firefox-enterprise"'
        )

    @override_settings(ZENDESK_CHAT_TAGS="")
    def test_the_product_tag_is_there_without_chat_tags(self):
        self.client.force_login(self.user)

        self.assertContains(self._get(), 'data-zendesk-chat-tags="product-firefox-enterprise"')

    def test_locale_is_set_to_the_page_locale(self):
        self.client.force_login(self.user)

        self.assertContains(self._get(), "'locale', 'en-US')")
        self.assertContains(self._get(locale="de"), "'locale', 'de')")

    def test_a_locale_zendesk_does_not_support_still_gets_the_widget_in_english(self):
        self.client.force_login(self.user)
        response = self._get(locale="fr")

        self.assertContains(response, SNIPPET_MARKER)
        self.assertContains(response, "'locale', 'en-US')")

    def test_no_snippet_for_anonymous_users(self):
        self.assertNotContains(self._get(), SNIPPET_MARKER)

    def test_no_snippet_for_a_user_without_chat_access(self):
        self.user.groups.clear()
        self.client.force_login(self.user)

        self.assertNotContains(self._get(), SNIPPET_MARKER)

    @override_switch("zendesk-chat", active=False)
    def test_no_snippet_when_the_switch_is_off(self):
        self.client.force_login(self.user)

        self.assertNotContains(self._get(), SNIPPET_MARKER)

    def test_a_chat_page_lets_the_widget_style_itself(self):
        self.client.force_login(self.user)

        sources = csp_directives(self._get()["Content-Security-Policy"])["style-src"]

        self.assertIn("'unsafe-inline'", sources)
        self.assertEqual([], [source for source in sources if source.startswith("'nonce-")])

    def test_a_chat_page_allows_the_zendesk_hosts(self):
        self.client.force_login(self.user)

        directives = csp_directives(self._get()["Content-Security-Policy"])

        self.assertIn("https://*.zdassets.com", directives["script-src"])
        self.assertIn("wss://*.zendesk.com", directives["connect-src"])

    def test_a_page_without_chat_names_no_zendesk_host(self):
        directives = csp_directives(self._get()["Content-Security-Policy"])

        self.assertNotIn("https://*.zdassets.com", directives["script-src"])
        self.assertNotIn("wss://*.zendesk.com", directives["connect-src"])

    def test_a_page_without_chat_keeps_the_style_nonce(self):
        sources = csp_directives(self._get()["Content-Security-Policy"])["style-src"]

        self.assertNotIn("'unsafe-inline'", sources)
        self.assertNotEqual([], [source for source in sources if source.startswith("'nonce-")])
