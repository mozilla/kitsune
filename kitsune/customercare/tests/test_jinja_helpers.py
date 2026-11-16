from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import override_settings
from waffle.testutils import override_switch

from kitsune.customercare.templatetags.jinja_helpers import chat_is_available
from kitsune.products.tests import SupportCoverageFactory
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
        coverage = SupportCoverageFactory(includes_chat=True)
        self.product = coverage.product
        self.user = UserFactory()
        self.user.groups.add(coverage.contract.company.group)

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
