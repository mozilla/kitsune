from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser

from kitsune.customercare import ZENDESK_CATEGORIES, ZENDESK_CATEGORIES_LOGINLESS
from kitsune.customercare.forms import ZendeskForm
from kitsune.customercare.models import SupportTicket
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class ZendeskFormTests(TestCase):
    """Tests for ZendeskForm with new product-specific categories."""

    def setUp(self):
        """Set up test data."""
        self.vpn_product = ProductFactory(title="Mozilla VPN", slug="mozilla-vpn", codename="vpn")
        self.relay_product = ProductFactory(title="Firefox Relay", slug="relay", codename="relay")
        self.accounts_product = ProductFactory(
            title="Mozilla Accounts", slug="mozilla-account", codename="accounts"
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

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
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

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_collects_all_tags_from_selected_category(self, mock_task):
        """Test that send() method collects all tags from selected category."""
        form = ZendeskForm(
            data={
                "email": "test@example.com",
                "category": "vpn-connection-issues",
                "subject": "Test subject",
                "description": "Test description",
                "country": "US",
            },
            product=self.vpn_product,
            user=self.user,
        )

        self.assertTrue(form.is_valid())
        submission = form.send(self.user, self.vpn_product)

        expected_tags = [
            "technical",  # legacy
            "t1-performance-and-connectivity",  # tier1
            "t2-connectivity",  # tier2
            "t3-connection-failure",  # tier3
            "ssa-connection-issues-automation",  # automation
        ]

        self.assertIsInstance(submission, SupportTicket)
        self.assertEqual(submission.zendesk_tags, expected_tags)
        self.assertEqual(submission.status, SupportTicket.STATUS_PENDING)
        self.assertEqual(submission.subject, "Test subject")
        self.assertEqual(submission.description, "Test description")
        self.assertEqual(submission.category, "vpn-connection-issues")
        self.assertEqual(submission.email, "test@example.com")
        self.assertEqual(submission.country, "US")
        self.assertEqual(submission.product, self.vpn_product)
        self.assertEqual(submission.user, self.user)
        mock_task.assert_called_once_with(submission.id)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_handles_categories_with_segmentation_tags(self, mock_task):
        """Test that segmentation tags are included when present."""
        form = ZendeskForm(
            data={
                "email": "test@example.com",
                "category": "relay-email-forwarding",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.relay_product,
            user=self.user,
        )

        self.assertTrue(form.is_valid())
        submission = form.send(self.user, self.relay_product)

        expected_tags = [
            "technical",  # legacy
            "t1-privacy-and-security",  # tier1
            "t2-masking",  # tier2
            "t3-email-masking",  # tier3
            "seg-relay-no-fwd-deliver",  # segmentation
        ]

        self.assertIsInstance(submission, SupportTicket)
        self.assertEqual(submission.zendesk_tags, expected_tags)
        self.assertEqual(submission.status, SupportTicket.STATUS_PENDING)
        mock_task.assert_called_once_with(submission.id)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_handles_categories_with_only_some_tags(self, mock_task):
        """Test that only non-null tags are collected."""
        form = ZendeskForm(
            data={
                "email": "test@example.com",
                "category": "payments",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.vpn_product,
            user=self.user,
        )

        self.assertTrue(form.is_valid())
        submission = form.send(self.user, self.vpn_product)

        expected_tags = ["payments", "t1-billing-and-subscriptions"]

        self.assertIsInstance(submission, SupportTicket)
        self.assertEqual(submission.zendesk_tags, expected_tags)
        self.assertEqual(submission.status, SupportTicket.STATUS_PENDING)
        mock_task.assert_called_once_with(submission.id)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_with_no_category_selected(self, mock_task):
        """Test that no tags are collected when no category is selected."""
        form = ZendeskForm(
            data={
                "email": "test@example.com",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.vpn_product,
            user=self.user,
        )

        if not form.is_valid():
            form.cleaned_data = {
                "email": "test@example.com",
                "subject": "Test subject",
                "description": "Test description",
                "category": "",  # Empty category
            }
        submission = form.send(self.user, self.vpn_product)

        self.assertIsInstance(submission, SupportTicket)
        self.assertEqual(submission.zendesk_tags, [])
        self.assertEqual(submission.status, SupportTicket.STATUS_PENDING)
        self.assertEqual(submission.category, "")
        mock_task.assert_called_once_with(submission.id)

    def test_product_without_categories_gets_empty_choices(self):
        """Test that products not in our categories dict get empty choices."""
        unknown_product = ProductFactory(
            title="Unknown Product", slug="unknown-product", codename="unknown"
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
        self.assertEqual(
            payments_category["topic"], "I need help with a billing or subscription question"
        )
        self.assertEqual(payments_category["tags"]["tiers"], ["t1-billing-and-subscriptions"])
        self.assertIsNone(payments_category["tags"]["automation"])
        self.assertIsNone(payments_category["tags"]["segmentation"])

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_loginless_send_uses_stored_categories(self, mock_task):
        """Test that loginless send() uses categories stored in init."""
        anonymous_user = AnonymousUser()
        form = ZendeskForm(
            data={
                "email": "test@example.com",
                "category": "fxa-2fa-lockout",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.accounts_product,
            user=anonymous_user,
        )

        self.assertTrue(form.is_valid())
        submission = form.send(anonymous_user, self.accounts_product)

        expected_tags = [
            "accounts",
            "t1-passwords-and-sign-in",
            "t2-two-factor-authentication",
            "t3-two-factor-lockout",
            "ssa-2fa-automation",
        ]

        self.assertIsInstance(submission, SupportTicket)
        self.assertEqual(submission.zendesk_tags, expected_tags)
        self.assertEqual(submission.status, SupportTicket.STATUS_PENDING)
        self.assertEqual(submission.user, None)  # Anonymous users don't have a user
        self.assertEqual(submission.email, "test@example.com")
        mock_task.assert_called_once_with(submission.id)
