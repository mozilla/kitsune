from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from waffle.testutils import override_switch

from kitsune.customercare.templatetags.jinja_helpers import (
    chat_is_available,
    select_zendesk_locale,
)
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

    def _request(self, user=None):
        return SimpleNamespace(user=user or self.user)

    def test_entitled_user(self):
        self.assertTrue(chat_is_available(self._request(), self.product))

    def test_page_that_is_not_about_a_product(self):
        self.assertFalse(chat_is_available(self._request(), None))

    def test_user_without_chat_access(self):
        self.user.groups.clear()

        self.assertFalse(chat_is_available(self._request(), self.product))

    def test_anonymous_user(self):
        self.assertFalse(chat_is_available(self._request(user=AnonymousUser()), self.product))

    @override_switch("zendesk-chat", active=False)
    def test_switch_off(self):
        self.assertFalse(chat_is_available(self._request(), self.product))

    @override_settings(ZENDESK_CHAT_WIDGET_KEY="")
    def test_switched_on_but_not_configured(self):
        """This fails loudly on purpose, because it's a configuration mistake."""
        with self.assertRaises(ImproperlyConfigured):
            chat_is_available(self._request(), self.product)


@override_settings(ZENDESK_CHAT_SUPPORTED_NON_ENGLISH_LOCALES="de,pt-BR")
class SelectZendeskLocaleTests(TestCase):
    """Test the selection of a Zendesk locale based on the SUMO locale."""

    def test_english_keeps_its_case(self):
        self.assertEqual("en-US", select_zendesk_locale("en-US"))

    def test_other_supported_locales_are_lower_cased(self):
        self.assertEqual("de", select_zendesk_locale("de"))
        self.assertEqual("pt-br", select_zendesk_locale("pt-BR"))

    def test_unsupported_locales_default_to_english(self):
        self.assertEqual("en-US", select_zendesk_locale("fr"))
        self.assertEqual("en-US", select_zendesk_locale("zh-CN"))
