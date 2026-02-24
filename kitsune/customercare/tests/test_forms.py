from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser

from kitsune.customercare.forms import ZendeskForm
from kitsune.customercare.models import SupportTicket
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    ZendeskConfigFactory,
    ZendeskTopicConfigurationFactory,
    ZendeskTopicFactory,
)
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

        # Create ZendeskConfig for VPN
        self.vpn_zendesk = ZendeskConfigFactory(name="Mozilla VPN Support")
        vpn_topic1 = ZendeskTopicFactory(
            slug="vpn-connection-issues",
            topic="I can't connect to Mozilla VPN",
            legacy_tag="technical",
            tier_tags=[
                "t1-performance-and-connectivity",
                "t2-connectivity",
                "t3-connection-failure",
            ],
            automation_tag="ssa-connection-issues-automation",
            segmentation_tag="",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk,
            zendesk_topic=vpn_topic1,
            display_order=0,
            loginless_only=False,
        )
        vpn_topic2 = ZendeskTopicFactory(
            slug="vpn-server-selection",
            topic="I can't choose a VPN location",
            legacy_tag="technical",
            tier_tags=[
                "t1-performance-and-connectivity",
                "t2-connectivity",
                "t3-cant-select-server",
            ],
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk,
            zendesk_topic=vpn_topic2,
            display_order=1,
            loginless_only=False,
        )
        vpn_topic3 = ZendeskTopicFactory(
            slug="payments",
            topic="I need help with a billing or subscription question",
            legacy_tag="payments",
            tier_tags=["t1-billing-and-subscriptions"],
            automation_tag="",
            segmentation_tag="",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.vpn_zendesk,
            zendesk_topic=vpn_topic3,
            display_order=2,
            loginless_only=False,
        )
        ProductSupportConfigFactory(
            product=self.vpn_product, zendesk_config=self.vpn_zendesk, forum_config=None
        )

        # Create ZendeskConfig for Relay
        self.relay_zendesk = ZendeskConfigFactory(name="Firefox Relay Support")
        relay_topic1 = ZendeskTopicFactory(
            slug="relay-email-forwarding",
            topic="I'm not receiving emails to my Relay mask",
            legacy_tag="technical",
            tier_tags=["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
            segmentation_tag="seg-relay-no-fwd-deliver",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.relay_zendesk,
            zendesk_topic=relay_topic1,
            display_order=0,
            loginless_only=False,
        )
        relay_topic2 = ZendeskTopicFactory(
            slug="relay-domain-change",
            topic="I want to change my Relay email domain",
            legacy_tag="technical",
            tier_tags=["t1-privacy-and-security", "t2-masking", "t3-email-masking"],
            segmentation_tag="seg-relay-chg-domain",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.relay_zendesk,
            zendesk_topic=relay_topic2,
            display_order=1,
            loginless_only=False,
        )
        ProductSupportConfigFactory(
            product=self.relay_product, zendesk_config=self.relay_zendesk, forum_config=None
        )

        # Create ZendeskConfig for Mozilla Account with loginless topics
        self.accounts_zendesk = ZendeskConfigFactory(name="Mozilla Account Support")
        accounts_topic1 = ZendeskTopicFactory(
            slug="fxa-2fa-lockout",
            topic="My security code isn't working or is lost",
            legacy_tag="accounts",
            tier_tags=[
                "t1-passwords-and-sign-in",
                "t2-two-factor-authentication",
                "t3-two-factor-lockout",
            ],
            automation_tag="ssa-2fa-automation",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.accounts_zendesk,
            zendesk_topic=accounts_topic1,
            display_order=0,
            loginless_only=True,
        )
        accounts_topic2 = ZendeskTopicFactory(
            slug="fxa-reset-password",
            topic="I forgot my password",
            legacy_tag="accounts",
            tier_tags=["t1-passwords-and-sign-in", "t2-reset-passwords"],
            automation_tag="ssa-emailverify-automation",
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.accounts_zendesk,
            zendesk_topic=accounts_topic2,
            display_order=1,
            loginless_only=True,
        )
        ProductSupportConfigFactory(
            product=self.accounts_product, zendesk_config=self.accounts_zendesk, forum_config=None
        )

    def test_authenticated_form_gets_correct_categories(self):
        """Test that authenticated users get product-specific categories."""
        form = ZendeskForm(product=self.vpn_product, user=self.user)

        category_topics = [choice[1] for choice in form.fields["category"].choices if choice[0]]
        self.assertIn("I can't connect to Mozilla VPN", category_topics)
        self.assertIn("I can't choose a VPN location", category_topics)
        self.assertEqual(len(category_topics), 3)  # 3 topics for VPN

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

        category_topics = [choice[1] for choice in form.fields["category"].choices if choice[0]]
        self.assertIn("I forgot my password", category_topics)
        self.assertIn("My security code isn't working or is lost", category_topics)
        self.assertEqual(len(category_topics), 2)  # 2 loginless topics for Mozilla Account

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
        """Test that products without ProductSupportConfig get no choices."""
        unknown_product = ProductFactory(
            title="Unknown Product", slug="unknown-product", codename="unknown"
        )

        form = ZendeskForm(product=unknown_product, user=self.user)

        category_choices = form.fields["category"].choices
        # Without ProductSupportConfig, no categories are populated
        self.assertEqual(len(category_choices), 0)

    def test_base_categories_are_properly_expanded(self):
        """Test that topics are properly loaded from database."""
        form = ZendeskForm(product=self.vpn_product, user=self.user)

        category_choices = form.fields["category"].choices
        category_dict = {slug: topic for slug, topic in category_choices if slug}

        self.assertIn("payments", category_dict)
        self.assertEqual(
            category_dict["payments"], "I need help with a billing or subscription question"
        )

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

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    def test_invalid_email_with_trailing_numbers(self):
        """Test that emails with trailing numbers are rejected (issue 2669)."""
        anonymous_user = AnonymousUser()
        form = ZendeskForm(
            data={
                "email": "frvv4@gmail.com8050262430",
                "category": "fxa-2fa-lockout",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.accounts_product,
            user=anonymous_user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("valid email address", str(form.errors["email"]))

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    def test_invalid_email_with_multiple_at_signs(self):
        """Test that emails with multiple @ signs are rejected."""
        anonymous_user = AnonymousUser()
        form = ZendeskForm(
            data={
                "email": "test@@example.com",
                "category": "fxa-2fa-lockout",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.accounts_product,
            user=anonymous_user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    def test_invalid_email_with_spaces(self):
        """Test that emails with spaces are rejected."""
        anonymous_user = AnonymousUser()
        form = ZendeskForm(
            data={
                "email": "test @example.com",
                "category": "fxa-2fa-lockout",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.accounts_product,
            user=anonymous_user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    @patch("django.conf.settings.LOGIN_EXCEPTIONS", ["mozilla-account"])
    def test_valid_email_passes_validation(self):
        """Test that valid emails pass validation."""
        anonymous_user = AnonymousUser()
        form = ZendeskForm(
            data={
                "email": "valid.email+tag@example.com",
                "category": "fxa-2fa-lockout",
                "subject": "Test subject",
                "description": "Test description",
            },
            product=self.accounts_product,
            user=anonymous_user,
        )

        self.assertTrue(form.is_valid())

    def test_deployment_fields_hidden_by_default(self):
        """Test that deployment fields are hidden when not enabled."""
        form = ZendeskForm(product=self.vpn_product, user=self.user)

        self.assertEqual(form.fields["update_channel"].widget.__class__.__name__, "HiddenInput")
        self.assertEqual(
            form.fields["policy_distribution"].widget.__class__.__name__, "HiddenInput"
        )
        self.assertFalse(form.fields["update_channel"].required)
        self.assertFalse(form.fields["policy_distribution"].required)

    def test_deployment_fields_shown_when_enabled(self):
        """Test that deployment fields are shown, required, and have choices when enabled."""
        self.vpn_zendesk.enable_deployment_fields = True
        self.vpn_zendesk.save()

        form = ZendeskForm(product=self.vpn_product, user=self.user)

        self.assertEqual(form.fields["update_channel"].widget.__class__.__name__, "Select")
        self.assertEqual(form.fields["policy_distribution"].widget.__class__.__name__, "Select")
        self.assertTrue(form.fields["update_channel"].required)
        self.assertTrue(form.fields["policy_distribution"].required)

        update_channel_values = [v for v, _ in form.fields["update_channel"].widget.choices if v]
        self.assertIn("esr", update_channel_values)
        self.assertIn("beta", update_channel_values)

        policy_values = [v for v, _ in form.fields["policy_distribution"].widget.choices if v]
        self.assertIn("group_policy_admx", policy_values)
        self.assertIn("autoconfig", policy_values)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_send_stores_deployment_fields(self, mock_task):
        """Test that deployment field values are stored in SupportTicket."""
        self.vpn_zendesk.enable_deployment_fields = True
        self.vpn_zendesk.save()

        form = ZendeskForm(
            data={
                "email": "test@example.com",
                "category": "vpn-connection-issues",
                "subject": "Test subject",
                "description": "Test description",
                "update_channel": "esr",
                "policy_distribution": "group_policy_admx",
            },
            product=self.vpn_product,
            user=self.user,
        )

        self.assertTrue(form.is_valid())
        submission = form.send(self.user, self.vpn_product)

        self.assertEqual(submission.update_channel, "esr")
        self.assertEqual(submission.policy_distribution, "group_policy_admx")
        mock_task.assert_called_once_with(submission.id)
