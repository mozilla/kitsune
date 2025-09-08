from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser

from kitsune.customercare import ZENDESK_CATEGORIES, ZENDESK_CATEGORIES_LOGINLESS
from kitsune.customercare.forms import ZendeskForm
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class ZendeskFormTests(TestCase):
    """Tests for ZendeskForm with new product-specific categories."""

    def setUp(self):
        """Set up test data."""
        self.vpn_product = ProductFactory(
            title="Mozilla VPN",
            slug="mozilla-vpn",
            codename="vpn"
        )
        self.relay_product = ProductFactory(
            title="Firefox Relay",
            slug="firefox-relay",
            codename="relay"
        )
        self.accounts_product = ProductFactory(
            title="Mozilla Accounts",
            slug="mozilla-account",
            codename="accounts"
        )
        self.user = UserFactory(email="test@example.com")

    def test_authenticated_form_gets_correct_categories(self):
        """Test that authenticated users get product-specific categories."""
        form = ZendeskForm(product=self.vpn_product, user=self.user)

        expected_categories = ZENDESK_CATEGORIES["mozilla-vpn"]
        self.assertEqual(form.product_categories, expected_categories)

        category_topics = [choice[1] for choice in form.fields["category"].choices if choice[0]]
        self.assertIn("I can't connect to Mozilla VPN", category_topics)
        self.assertIn("I can't choose a VPN location", category_topics)

    def test_different_products_get_different_categories(self):
        """Test that different products get different categories."""
        vpn_form = ZendeskForm(product=self.vpn_product, user=self.user)
        relay_form = ZendeskForm(product=self.relay_product, user=self.user)

        vpn_topics = [choice[1] for choice in vpn_form.fields["category"].choices if choice[0]]
        relay_topics = [choice[1] for choice in relay_form.fields["category"].choices if choice[0]]

        self.assertIn("I can't choose a VPN location", vpn_topics)
        self.assertNotIn("I can't choose a VPN location", relay_topics)
        self.assertIn("I want to change my Relay email domain", relay_topics)
        self.assertNotIn("I want to change my Relay email domain", vpn_topics)

    @patch('django.conf.settings.LOGIN_EXCEPTIONS', ['mozilla-account'])
    def test_loginless_form_gets_loginless_categories(self):
        """Test that loginless users get FxA-specific categories."""
        anonymous_user = AnonymousUser()
        form = ZendeskForm(product=self.accounts_product, user=anonymous_user)

        expected_categories = ZENDESK_CATEGORIES_LOGINLESS["mozilla-account"]
        self.assertEqual(form.product_categories, expected_categories)

        category_topics = [choice[1] for choice in form.fields["category"].choices if choice[0]]
        self.assertIn("I forgot my password", category_topics)
        self.assertIn("My security code isn't working or is lost", category_topics)

    def test_form_stores_product_and_user(self):
        """Test that form stores product and user for later use."""
        form = ZendeskForm(product=self.vpn_product, user=self.user)

        self.assertEqual(form.product, self.vpn_product)
        self.assertEqual(form.user, self.user)

    @patch('kitsune.customercare.forms.ZendeskClient')
    def test_send_collects_all_tags_from_selected_category(self, mock_client_class):
        """Test that send() method collects all tags from selected category."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        form = ZendeskForm(
            data={
                'email': 'test@example.com',
                'category': 'accounts',
                'subject': 'Test subject',
                'description': 'Test description',
                'country': 'US'
            },
            product=self.vpn_product,
            user=self.user
        )

        self.assertTrue(form.is_valid())
        form.send(self.user, self.vpn_product)

        expected_tags = [
            "accounts",  # legacy
            "t1-passwords-and-sign-in",  # tier1
            "t2-sign-in",  # tier2
            "t3-sign-in-failure",  # tier3
            "ssa-sign-in-failure-automation"  # automation
        ]
        self.assertEqual(form.cleaned_data["zendesk_tags"], expected_tags)
        mock_client.create_ticket.assert_called_once_with(self.user, form.cleaned_data)

    @patch('kitsune.customercare.forms.ZendeskClient')
    def test_send_handles_categories_with_segmentation_tags(self, mock_client_class):
        """Test that segmentation tags are included when present."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        form = ZendeskForm(
            data={
                'email': 'test@example.com',
                'category': 'technical',
                'subject': 'Test subject',
                'description': 'Test description',
            },
            product=self.relay_product,
            user=self.user
        )

        self.assertTrue(form.is_valid())
        form.send(self.user, self.relay_product)

        expected_tags = [
            "technical",  # legacy
            "t1-privacy-and-security",  # tier1
            "t2-masking",  # tier2
            "t3-email-masking",  # tier3
            "seg-relay-no-fwd-deliver"  # segmentation
        ]
        self.assertEqual(form.cleaned_data["zendesk_tags"], expected_tags)

    @patch('kitsune.customercare.forms.ZendeskClient')
    def test_send_handles_categories_with_only_some_tags(self, mock_client_class):
        """Test that only non-null tags are collected."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        form = ZendeskForm(
            data={
                'email': 'test@example.com',
                'category': 'payments',
                'subject': 'Test subject',
                'description': 'Test description',
            },
            product=self.vpn_product,
            user=self.user
        )

        self.assertTrue(form.is_valid())
        form.send(self.user, self.vpn_product)

        expected_tags = [
            "payments",
            "t1-billing-and-subscriptions"
        ]
        self.assertEqual(form.cleaned_data["zendesk_tags"], expected_tags)

    @patch('kitsune.customercare.forms.ZendeskClient')
    def test_send_with_no_category_selected(self, mock_client_class):
        """Test that no tags are collected when no category is selected."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        form = ZendeskForm(
            data={
                'email': 'test@example.com',
                'subject': 'Test subject',
                'description': 'Test description',
            },
            product=self.vpn_product,
            user=self.user
        )

        if not form.is_valid():
            form.cleaned_data = {
                'email': 'test@example.com',
                'subject': 'Test subject',
                'description': 'Test description',
            }
        form.send(self.user, self.vpn_product)
        self.assertNotIn("zendesk_tags", form.cleaned_data)

    def test_product_without_categories_gets_empty_choices(self):
        """Test that products not in our categories dict get empty choices."""
        unknown_product = ProductFactory(
            title="Unknown Product",
            slug="unknown-product",
            codename="unknown"
        )

        form = ZendeskForm(product=unknown_product, user=self.user)

        category_choices = form.fields["category"].choices
        self.assertEqual(len(category_choices), 1)
        self.assertEqual(category_choices[0][1], "Select a reason for contacting")

    def test_base_categories_are_properly_expanded(self):
        """Test that DRY base categories are properly expanded."""
        form = ZendeskForm(product=self.vpn_product, user=self.user)

        payments_category = None
        for category in form.product_categories:
            if category["slug"] == "payments":
                payments_category = category
                break

        self.assertIsNotNone(payments_category)
        self.assertEqual(payments_category["topic"], "I need help with a billing or subscription question")
        self.assertEqual(payments_category["tags"]["legacy"], "payments")
        self.assertEqual(payments_category["tags"]["tiers"], ["t1-billing-and-subscriptions"])
        self.assertIsNone(payments_category["tags"]["automation"])
        self.assertIsNone(payments_category["tags"]["segmentation"])

    @patch('django.conf.settings.LOGIN_EXCEPTIONS', ['mozilla-account'])
    @patch('kitsune.customercare.forms.ZendeskClient')
    def test_loginless_send_uses_stored_categories(self, mock_client_class):
        """Test that loginless send() uses categories stored in init."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        anonymous_user = AnonymousUser()
        form = ZendeskForm(
            data={
                'email': 'test@example.com',
                'category': 'fxa-2fa-lockout',
                'subject': 'Test subject',
                'description': 'Test description',
            },
            product=self.accounts_product,
            user=anonymous_user
        )

        self.assertTrue(form.is_valid())
        form.send(anonymous_user, self.accounts_product)

        expected_tags = [
            "accounts",
            "t1-passwords-and-sign-in",
            "t2-two-factor-authentication",
            "t3-two-factor-lockout",
            "ssa-2fa-automation"
        ]
        self.assertEqual(form.cleaned_data["zendesk_tags"], expected_tags)
