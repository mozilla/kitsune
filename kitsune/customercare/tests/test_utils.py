from unittest.mock import Mock, patch

from zenpy.lib.exception import APIException

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.utils import (
    _topic_to_tag,
    generate_classification_tags,
    send_support_ticket_to_zendesk,
)
from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.tests import TestCase


class TopicToTagTests(TestCase):
    """Tests for _topic_to_tag helper function."""

    def test_lowercase_conversion(self):
        """Test that titles are converted to lowercase."""
        self.assertEqual(_topic_to_tag("Settings"), "settings")
        self.assertEqual(_topic_to_tag("ACCOUNTS"), "accounts")

    def test_spaces_to_dashes(self):
        """Test that spaces are replaced with dashes."""
        self.assertEqual(_topic_to_tag("Sign in"), "sign-in")
        self.assertEqual(_topic_to_tag("Two factor authentication"), "two-factor-authentication")

    def test_remove_commas(self):
        """Test that commas are removed."""
        self.assertEqual(
            _topic_to_tag("Addons, extensions, and themes"), "addons-extensions-and-themes"
        )

    def test_remove_periods(self):
        """Test that periods are removed."""
        self.assertEqual(_topic_to_tag("F.O.O"), "foo")

    def test_complex_example(self):
        """Test complex title with multiple transformations."""
        self.assertEqual(
            _topic_to_tag("Addons, extensions, and themes"), "addons-extensions-and-themes"
        )


class GenerateClassificationTagsTests(TestCase):
    """Tests for generate_classification_tags function."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="firefox", title="Firefox")

    def test_no_topic_result_returns_undefined(self):
        """Test that missing topic_result returns ['undefined', 'general']."""
        submission = Mock(product=self.product)
        result = {}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])

    def test_undefined_topic_returns_empty_list(self):
        """Test that 'Undefined' topic returns ['undefined', 'general']."""
        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Undefined"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])

    def test_topic_not_found_in_db_returns_undefined(self):
        """Test that topic not found in database returns ['undefined', 'general']."""
        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Nonexistent Topic"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])

    def test_single_tier_topic(self):
        """Test generating tags for a tier 1 topic."""
        topic = TopicFactory(title="Settings", parent=None, is_archived=False)
        topic.products.add(self.product)

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Settings"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-settings", "technical"])

    def test_two_tier_topic(self):
        """Test generating tags for a tier 2 topic."""
        tier1 = TopicFactory(title="Settings", parent=None, is_archived=False)
        tier1.products.add(self.product)
        tier2 = TopicFactory(title="Notifications", parent=tier1, is_archived=False)
        tier2.products.add(self.product)

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Notifications"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-settings", "t2-notifications", "technical"])

    def test_three_tier_topic(self):
        """Test generating tags for a tier 3 topic."""
        tier1 = TopicFactory(title="Settings", parent=None, is_archived=False)
        tier1.products.add(self.product)
        tier2 = TopicFactory(
            title="Addons, extensions, and themes", parent=tier1, is_archived=False
        )
        tier2.products.add(self.product)
        tier3 = TopicFactory(title="Extensions", parent=tier2, is_archived=False)
        tier3.products.add(self.product)

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Extensions"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(
            tags, ["t1-settings", "t2-addons-extensions-and-themes", "t3-extensions", "technical"]
        )

    @patch("kitsune.customercare.utils.ZENDESK_CATEGORIES")
    def test_automation_tag_included_when_matched(self, mock_categories):
        """Test that automation tag is included when tier tags match a category."""
        mock_categories.get.return_value = [
            {
                "slug": "accounts-signin",
                "tags": {
                    "tiers": ["t1-passwords-and-sign-in", "t2-sign-in"],
                    "automation": "ssa-sign-in-failure-automation",
                },
            }
        ]

        tier1 = TopicFactory(title="Passwords and sign in", parent=None, is_archived=False)
        tier1.products.add(self.product)
        tier2 = TopicFactory(title="Sign in", parent=tier1, is_archived=False)
        tier2.products.add(self.product)

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Sign in"}}

        tags = generate_classification_tags(submission, result)

        self.assertIn("ssa-sign-in-failure-automation", tags)
        self.assertIn("t1-passwords-and-sign-in", tags)
        self.assertIn("t2-sign-in", tags)
        self.assertIn("accounts", tags)

    @patch("kitsune.customercare.utils.ZENDESK_CATEGORIES")
    def test_no_automation_tag_when_not_matched(self, mock_categories):
        """Test that no automation tag is included when tier tags don't match."""
        mock_categories.get.return_value = [
            {
                "slug": "different-category",
                "tags": {
                    "tiers": ["t1-different"],
                    "automation": "some-automation",
                },
            }
        ]

        tier1 = TopicFactory(title="Billing and subscriptions", parent=None, is_archived=False)
        tier1.products.add(self.product)

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Billing and subscriptions"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-billing-and-subscriptions", "payment"])
        self.assertNotIn("some-automation", tags)

    def test_product_reassignment_includes_other_tag(self):
        """Test that product reassignment adds 'other' tag."""
        tier1 = TopicFactory(title="Settings", parent=None, is_archived=False)
        tier1.products.add(self.product)

        submission = Mock(product=self.product)
        result = {
            "product_result": {"product": "Mozilla VPN"},
            "topic_result": {"topic": "Settings"},
        }

        tags = generate_classification_tags(submission, result)

        self.assertIn("other", tags)
        self.assertIn("t1-settings", tags)
        self.assertIn("technical", tags)

    def test_archived_topic_returns_undefined(self):
        """Test that archived topics are not found and return ['undefined', 'general']."""
        topic = TopicFactory(title="Settings", parent=None, is_archived=True)
        topic.products.add(self.product)

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Settings"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])


class SendSupportTicketToZendeskTests(TestCase):
    """Tests for send_support_ticket_to_zendesk error handling."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="mozilla-vpn", title="Mozilla VPN")
        self.submission = Mock(spec=SupportTicket)
        self.submission.product = self.product
        self.submission.user = None
        self.submission.subject = "Test"
        self.submission.description = "Test description"
        self.submission.category = "test"
        self.submission.email = "test@example.com"
        self.submission.os = "win10"
        self.submission.country = "US"
        self.submission.zendesk_tags = []

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_suspended_user_error_auto_rejects(self, mock_zendesk_client):
        """Test that UserSuspended errors result in auto-rejection (issue 2670)."""
        mock_client = mock_zendesk_client.return_value
        error = APIException(
            '{"error": "RecordInvalid", "description": "Record validation errors", "details": {"requester": [{"description": "Requester: test@example.com is suspended.", "error": "UserSuspended"}]}}'
        )
        mock_client.create_ticket.side_effect = error

        result = send_support_ticket_to_zendesk(self.submission)

        self.assertFalse(result)
        self.assertEqual(self.submission.status, SupportTicket.STATUS_REJECTED)
        self.submission.save.assert_called_with(update_fields=["status"])

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_record_invalid_email_error_auto_rejects(self, mock_zendesk_client):
        """Test that RecordInvalid errors for email result in auto-rejection (issue 2669)."""
        mock_client = mock_zendesk_client.return_value
        error = APIException(
            '{"error": "RecordInvalid", "description": "Record validation errors", "details": {"email": ["Email is not properly formatted"]}}'
        )
        mock_client.create_ticket.side_effect = error

        result = send_support_ticket_to_zendesk(self.submission)

        self.assertFalse(result)
        self.assertEqual(self.submission.status, SupportTicket.STATUS_REJECTED)
        self.submission.save.assert_called_with(update_fields=["status"])

    @patch("kitsune.customercare.utils.flag_object")
    @patch("kitsune.customercare.utils.Profile")
    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_other_api_exception_flags_for_review(
        self, mock_zendesk_client, mock_profile, mock_flag_object
    ):
        """Test that other APIExceptions are flagged for manual review."""
        mock_client = mock_zendesk_client.return_value
        error = APIException("Some other API error")
        mock_client.create_ticket.side_effect = error

        result = send_support_ticket_to_zendesk(self.submission)

        self.assertFalse(result)
        self.assertEqual(self.submission.status, SupportTicket.STATUS_FLAGGED)
        self.submission.save.assert_called_with(update_fields=["status"])
        mock_flag_object.assert_called_once()

    @patch("kitsune.customercare.utils.flag_object")
    @patch("kitsune.customercare.utils.Profile")
    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_generic_exception_flags_for_review(
        self, mock_zendesk_client, mock_profile, mock_flag_object
    ):
        """Test that generic exceptions are flagged for manual review."""
        mock_client = mock_zendesk_client.return_value
        error = Exception("Unexpected error")
        mock_client.create_ticket.side_effect = error

        result = send_support_ticket_to_zendesk(self.submission)

        self.assertFalse(result)
        self.assertEqual(self.submission.status, SupportTicket.STATUS_FLAGGED)
        self.submission.save.assert_called_with(update_fields=["status"])
        mock_flag_object.assert_called_once()

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_successful_submission(self, mock_zendesk_client):
        """Test successful ticket submission."""
        mock_client = mock_zendesk_client.return_value
        mock_ticket_audit = Mock()
        mock_ticket_audit.ticket.id = 12345
        mock_client.create_ticket.return_value = mock_ticket_audit

        result = send_support_ticket_to_zendesk(self.submission)

        self.assertTrue(result)
        self.assertEqual(self.submission.zendesk_ticket_id, "12345")
        self.assertEqual(self.submission.status, SupportTicket.STATUS_SENT)
        self.submission.save.assert_called_with(update_fields=["zendesk_ticket_id", "status"])
