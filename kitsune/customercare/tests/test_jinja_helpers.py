from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from waffle.testutils import override_switch

from kitsune.customercare.templatetags.jinja_helpers import chat_is_available, to_zendesk_locale
from kitsune.groups.models import GroupProfile
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    ZendeskConfigFactory,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


@override_switch("zendesk-chat", active=True)
@override_settings(
    ZENDESK_CHAT_WIDGET_KEY="test-widget-key",
    ZENDESK_CHAT_SIGNING_SECRET="test-signing-secret",
    ZENDESK_CHAT_SIGNING_KEY_ID="test-key-id",
    ZENDESK_CHAT_ENABLED_LOCALES=["en-US", "de"],
)
class ChatIsAvailableTests(TestCase):
    """Tests the gate deciding which pages get the chat widget."""

    def setUp(self):
        self.product = ProductFactory()
        config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=ZendeskConfigFactory()
        )
        root = GroupProfile.add_root(group=Group.objects.create(name="chat"), slug="chat")
        company = root.add_child(group=Group.objects.create(name="company"), slug="company")
        SupportOrganizationFactory(config=config, group=company.group, include_live_chat=True)
        self.user = UserFactory()
        self.user.groups.add(company.group)

    def _request(self, user=None, locale="en-US"):
        return SimpleNamespace(user=user or self.user, LANGUAGE_CODE=locale)

    def test_entitled_user(self):
        self.assertTrue(chat_is_available(self._request(), self.product))

    def test_page_that_is_not_about_a_product(self):
        self.assertFalse(chat_is_available(self._request(), None))

    @override_settings(ZENDESK_CHAT_WIDGET_KEY="")
    def test_a_page_without_a_product_does_not_care_about_the_configuration(self):
        self.assertFalse(chat_is_available(self._request(), None))

    def test_user_without_chat_access(self):
        self.user.groups.clear()

        self.assertFalse(chat_is_available(self._request(), self.product))

    def test_anonymous_user(self):
        self.assertFalse(chat_is_available(self._request(user=AnonymousUser()), self.product))

    def test_enabled_locale(self):
        self.assertTrue(chat_is_available(self._request(locale="de"), self.product))

    def test_locale_that_is_not_enabled(self):
        """Zendesk ignores a locale it doesn't know, so we hide chat rather than
        let the widget fall back to the browser's language."""
        self.assertFalse(chat_is_available(self._request(locale="fr"), self.product))

    @override_switch("zendesk-chat", active=False)
    def test_switch_off(self):
        self.assertFalse(chat_is_available(self._request(), self.product))

    @override_settings(ZENDESK_CHAT_WIDGET_KEY="")
    def test_switched_on_but_not_configured(self):
        """This fails loudly on purpose, because it's a configuration mistake."""
        with self.assertRaises(ImproperlyConfigured):
            chat_is_available(self._request(), self.product)


class ToZendeskLocaleTests(TestCase):
    """Zendesk's allowed locale list is lower case apart from en-US."""

    def test_english_keeps_its_case(self):
        self.assertEqual("en-US", to_zendesk_locale("en-US"))

    def test_other_locales_are_lower_cased(self):
        self.assertEqual("de", to_zendesk_locale("de"))
        self.assertEqual("pt-br", to_zendesk_locale("pt-BR"))
