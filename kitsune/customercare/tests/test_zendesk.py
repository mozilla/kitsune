from unittest.mock import Mock, patch

from kitsune.customercare.zendesk import LOGINLESS_TAG, ZendeskClient
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class ZendeskClientTests(TestCase):
    """Tests for ZendeskClient tag handling."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    def test_create_ticket_includes_zendesk_tags_for_authenticated_user(self, mock_zenpy):
        """Test that create_ticket includes taxonomy tags for authenticated users."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.tickets.create.return_value = Mock(id=789)
        self.user.profile.zendesk_id = "123"

        client = ZendeskClient()
        client.update_user = Mock(return_value=Mock(id=456))

        ticket_fields = {
            "product": "mozilla-vpn",
            "product_title": "Mozilla VPN",
            "subject": "Test subject",
            "description": "Test description",
            "category": "accounts",
            "os": "win10",
            "country": "US",
            "ticket_form_id": 456,
            "zendesk_tags": [
                "accounts",  # legacy
                "t1-passwords-and-sign-in",  # tier1
                "t2-sign-in",  # tier2
                "t3-sign-in-failure",  # tier3
                "ssa-sign-in-failure-automation",  # automation
            ],
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]  # First positional arg (the Ticket)

        expected_tags = [
            "accounts",
            "t1-passwords-and-sign-in",
            "t2-sign-in",
            "t3-sign-in-failure",
            "ssa-sign-in-failure-automation",
        ]
        self.assertEqual(call_args.tags, expected_tags)

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    @patch("django.conf.settings.ZENDESK_CONTACT_LABEL_ID", 127)
    def test_create_ticket_includes_loginless_tag_plus_zendesk_tags(self, mock_zenpy):
        """Test that loginless tickets include both loginless tag and taxonomy tags."""
        from django.contrib.auth.models import AnonymousUser

        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.tickets.create.return_value = Mock(id=789)

        client = ZendeskClient()
        client.create_user = Mock(return_value=Mock(id=456))

        anonymous_user = AnonymousUser()
        ticket_fields = {
            "product": "mozilla-account",
            "product_title": "Mozilla Accounts",
            "subject": "Test subject",
            "description": "Test description",
            "category": "fxa-2fa-lockout",
            "email": "test@example.com",
            "ticket_form_id": 456,
            "zendesk_tags": [
                "accounts",  # legacy
                "t1-passwords-and-sign-in",  # tier1
                "t2-two-factor-authentication",  # tier2
                "t3-two-factor-lockout",  # tier3
                "ssa-2fa-automation",  # automation
            ],
        }

        client.create_ticket(anonymous_user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]  # First positional arg (the Ticket)

        expected_tags = [
            LOGINLESS_TAG,  # loginless_ticket
            "accounts",
            "t1-passwords-and-sign-in",
            "t2-two-factor-authentication",
            "t3-two-factor-lockout",
            "ssa-2fa-automation",
        ]
        self.assertEqual(call_args.tags, expected_tags)

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    def test_create_ticket_without_zendesk_tags(self, mock_zenpy):
        """Test that tickets without zendesk_tags don't include extra tags."""
        # Mock the Zenpy client
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.tickets.create.return_value = Mock(id=789)

        self.user.profile.zendesk_id = "123"

        client = ZendeskClient()
        client.update_user = Mock(return_value=Mock(id=456))

        ticket_fields = {
            "product": "mozilla-vpn",
            "product_title": "Mozilla VPN",
            "subject": "Test subject",
            "description": "Test description",
            "category": "accounts",
            "os": "win10",
            "country": "US",
            "ticket_form_id": 456,
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]  # First positional arg (the Ticket)

        if hasattr(call_args, "tags"):
            self.assertIn(call_args.tags, [[], None])
        else:
            pass

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    def test_create_ticket_with_empty_zendesk_tags(self, mock_zenpy):
        """Test that tickets with empty zendesk_tags list don't include tags."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.tickets.create.return_value = Mock(id=789)

        self.user.profile.zendesk_id = "123"

        client = ZendeskClient()
        client.update_user = Mock(return_value=Mock(id=456))

        ticket_fields = {
            "product": "mozilla-vpn",
            "product_title": "Mozilla VPN",
            "subject": "Test subject",
            "description": "Test description",
            "category": "accounts",
            "os": "win10",
            "country": "US",
            "ticket_form_id": 456,
            "zendesk_tags": [],  # Empty list
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]  # First positional arg (the Ticket)

        if hasattr(call_args, "tags"):
            self.assertIn(call_args.tags, [[], None])

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    @patch("django.conf.settings.ZENDESK_CONTACT_LABEL_ID", 127)
    def test_create_ticket_with_none_user(self, mock_zenpy):
        """Test that create_ticket works with user=None (loginless ticket)."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.tickets.create.return_value = Mock(id=789)

        client = ZendeskClient()
        client.create_user = Mock(return_value=Mock(id=456))

        ticket_fields = {
            "product": "mozilla-account",
            "product_title": "Mozilla Accounts",
            "subject": "Test subject",
            "description": "Test description",
            "category": "fxa-2fa-lockout",
            "email": "test@example.com",
            "ticket_form_id": 456,
            "zendesk_tags": ["accounts"],
        }

        # This should not raise AttributeError
        client.create_ticket(None, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]

        # Should include loginless tag
        self.assertIn(LOGINLESS_TAG, call_args.tags)

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    @patch("django.conf.settings.ZENDESK_UPDATE_CHANNEL_FIELD_ID", 127)
    @patch("django.conf.settings.ZENDESK_POLICY_DISTRIBUTION_FIELD_ID", 128)
    def test_create_ticket_includes_deployment_fields(self, mock_zenpy):
        """Test that create_ticket includes deployment fields when provided."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.tickets.create.return_value = Mock(id=789)
        self.user.profile.zendesk_id = "123"

        client = ZendeskClient()
        client.update_user = Mock(return_value=Mock(id=456))

        ticket_fields = {
            "product": "firefox",
            "product_title": "Firefox",
            "subject": "Test subject",
            "description": "Test description",
            "category": "technical",
            "os": "win10",
            "country": "US",
            "ticket_form_id": 456,
            "update_channel": "esr",
            "policy_distribution": "group_policy_admx",
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]

        custom_fields = call_args.custom_fields
        field_dict = {field["id"]: field["value"] for field in custom_fields}

        self.assertEqual(field_dict[127], "esr")
        self.assertEqual(field_dict[128], "group_policy_admx")

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    @patch("django.conf.settings.ZENDESK_UPDATE_CHANNEL_FIELD_ID", 127)
    @patch("django.conf.settings.ZENDESK_POLICY_DISTRIBUTION_FIELD_ID", 128)
    def test_create_ticket_omits_empty_deployment_fields(self, mock_zenpy):
        """Test that create_ticket omits deployment fields when not provided."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.tickets.create.return_value = Mock(id=789)
        self.user.profile.zendesk_id = "123"

        client = ZendeskClient()
        client.update_user = Mock(return_value=Mock(id=456))

        ticket_fields = {
            "product": "firefox",
            "product_title": "Firefox",
            "subject": "Test subject",
            "description": "Test description",
            "category": "technical",
            "os": "win10",
            "country": "US",
            "ticket_form_id": 456,
            "update_channel": "",
            "policy_distribution": "",
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]

        custom_fields = call_args.custom_fields
        field_ids = [field["id"] for field in custom_fields]

        self.assertNotIn(127, field_ids)
        self.assertNotIn(128, field_ids)
