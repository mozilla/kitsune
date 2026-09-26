import json
from base64 import b64decode
from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.checks import Warning
from django.test import SimpleTestCase, override_settings
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.checks import check_zendesk_oauth_configuration
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.zendesk import (
    LOGINLESS_TAG,
    ZendeskClient,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


def chat_ticket(id, status="open", channel=SupportTicket.ZD_CHANNEL_MESSAGING):
    return Mock(id=id, status=status, via=Mock(channel=channel))


@override_settings(
    ZENDESK_SUBDOMAIN="oauth-test",
    ZENDESK_OAUTH_CLIENT_ID="sumo",
    ZENDESK_OAUTH_CLIENT_SECRET="test-client-secret",
)
class ZendeskClientTests(TestCase):
    """Tests for ZendeskClient tag handling."""

    def setUp(self):
        """Set up test data."""
        self.user = UserFactory()
        token_patch = patch(
            "kitsune.customercare.zendesk.get_oauth_token", return_value="test-access-token"
        )
        token_patch.start()
        self.addCleanup(token_patch.stop)

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
            "os": "win64",
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
            "os": "win64",
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
            "os": "win64",
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
            "os": "win64",
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
    @patch("django.conf.settings.ZENDESK_URGENCY_FIELD_ID", 129)
    def test_create_ticket_includes_urgency(self, mock_zenpy):
        """Test that create_ticket includes urgency when provided."""
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
            "os": "win64",
            "country": "US",
            "ticket_form_id": 456,
            "urgency": "critical",
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]

        field_dict = {field["id"]: field["value"] for field in call_args.custom_fields}

        self.assertEqual(field_dict[129], "critical")

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    @patch("django.conf.settings.ZENDESK_URGENCY_FIELD_ID", 129)
    def test_create_ticket_omits_empty_urgency(self, mock_zenpy):
        """Test that create_ticket omits urgency when not provided."""
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
            "os": "win64",
            "country": "US",
            "ticket_form_id": 456,
            "urgency": "",
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]

        field_ids = [field["id"] for field in call_args.custom_fields]

        self.assertNotIn(129, field_ids)

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
            "os": "win64",
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

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    def test_create_ticket_includes_brand_id(self, mock_zenpy):
        """Test that create_ticket sets brand_id on the ticket when provided."""
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
            "os": "win64",
            "country": "US",
            "ticket_form_id": 456,
            "brand_id": "360000001234",
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]

        self.assertEqual(call_args.brand_id, 360000001234)

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_PRODUCT_FIELD_ID", 123)
    @patch("django.conf.settings.ZENDESK_OS_FIELD_ID", 124)
    @patch("django.conf.settings.ZENDESK_COUNTRY_FIELD_ID", 125)
    @patch("django.conf.settings.ZENDESK_CATEGORY_FIELD_ID", 126)
    def test_create_ticket_omits_brand_id_when_not_set(self, mock_zenpy):
        """Test that create_ticket does not set brand_id when not provided."""
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
            "os": "win64",
            "country": "US",
            "ticket_form_id": 456,
            "brand_id": "",
        }

        client.create_ticket(self.user, ticket_fields)

        mock_client.tickets.create.assert_called_once()
        call_args = mock_client.tickets.create.call_args[0][0]

        self.assertFalse(hasattr(call_args, "brand_id") and call_args.brand_id)

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_get_ticket(self, mock_zenpy):
        """Test that get_ticket fetches a ticket by ID."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_ticket = Mock(id=123, status="open", subject="Test ticket")
        mock_client.tickets.return_value = mock_ticket

        client = ZendeskClient()
        result = client.get_ticket(123)

        mock_client.tickets.assert_called_once_with(id=123)
        self.assertEqual(result, mock_ticket)

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_get_ticket_comments(self, mock_zenpy):
        """Test that get_ticket_comments returns a list of comments."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_comments = [Mock(body="First comment"), Mock(body="Second comment")]
        mock_client.tickets.comments.return_value = iter(mock_comments)

        client = ZendeskClient()
        result = client.get_ticket_comments(456)

        mock_client.tickets.comments.assert_called_once_with(ticket=456)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].body, "First comment")
        self.assertEqual(result[1].body, "Second comment")

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_public(self, mock_zenpy):
        """Test that add_ticket_comment adds a public comment."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        self.user.profile.zendesk_id = "789"

        client = ZendeskClient()
        client.add_ticket_comment(self.user, 123, "Hello there", public=True)

        ticket_arg = mock_client.tickets.update.call_args[0][0]
        self.assertEqual(ticket_arg.id, 123)
        self.assertEqual(ticket_arg.comment.body, "Hello there")
        self.assertTrue(ticket_arg.comment.public)
        self.assertEqual(ticket_arg.comment.author_id, 789)

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_private(self, mock_zenpy):
        """Test that add_ticket_comment adds a private comment."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        self.user.profile.zendesk_id = "789"

        client = ZendeskClient()
        client.add_ticket_comment(self.user, 123, "Internal note", public=False)

        ticket_arg = mock_client.tickets.update.call_args[0][0]
        self.assertEqual(ticket_arg.comment.body, "Internal note")
        self.assertFalse(ticket_arg.comment.public)
        self.assertEqual(ticket_arg.comment.author_id, 789)

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_without_status_does_not_set_ticket_status(self, mock_zenpy):
        """Test that add_ticket_comment leaves ticket status unset when status=None."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        self.user.profile.zendesk_id = "789"

        client = ZendeskClient()
        client.add_ticket_comment(self.user, 123, "Hello", status=None)

        ticket_arg = mock_client.tickets.update.call_args[0][0]
        self.assertIsNone(ticket_arg.status)

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_with_status_sets_ticket_status(self, mock_zenpy):
        """Test that add_ticket_comment sets ticket status when status is provided."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        self.user.profile.zendesk_id = "789"

        client = ZendeskClient()
        client.add_ticket_comment(self.user, 123, "Hello", status="open")

        ticket_arg = mock_client.tickets.update.call_args[0][0]
        self.assertEqual(ticket_arg.status, "open")
        self.assertEqual(ticket_arg.comment.body, "Hello")

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_creates_zendesk_user_if_missing(self, mock_zenpy):
        """Test that add_ticket_comment creates a Zendesk user when zendesk_id is missing."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client
        mock_client.users.create_or_update.return_value = Mock(id=999)
        self.user.profile.zendesk_id = ""

        client = ZendeskClient()
        client.add_ticket_comment(self.user, 123, "Comment")

        ticket_arg = mock_client.tickets.update.call_args[0][0]
        self.assertEqual(ticket_arg.comment.author_id, 999)

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_with_anonymous_user(self, mock_zenpy):
        """Test that add_ticket_comment raises ValueError for anonymous users."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()

        with self.assertRaises(ValueError):
            client.add_ticket_comment(AnonymousUser(), 123, "Anon comment")

        mock_client.tickets.update.assert_not_called()

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_update_ticket_status(self, mock_zenpy):
        """Test that update_ticket_status updates the status on a ticket."""
        mock_client = Mock()
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        client.update_ticket_status(123, "solved")

        ticket_arg = mock_client.tickets.update.call_args[0][0]
        self.assertEqual(ticket_arg.id, 123)
        self.assertEqual(ticket_arg.status, "solved")

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_keeps_only_the_users_active_chat_tickets(self, mock_zenpy):
        users = mock_zenpy.return_value.users
        chats = [chat_ticket(1, "new"), chat_ticket(2, "open"), chat_ticket(3, "pending")]
        chats += [chat_ticket(4, "hold")]
        users.requested.return_value = [
            *chats,
            chat_ticket(5, "solved"),
            chat_ticket(6, "closed"),
            chat_ticket(7, channel="web"),
        ]

        tickets = ZendeskClient().get_active_chat_tickets("789")

        self.assertEqual(tickets, chats)
        users.requested.assert_called_once_with(789)


@override_settings(
    ZENDESK_SUBDOMAIN="oauth-test",
    ZENDESK_USER_EMAIL="legacy@example.com",
    ZENDESK_API_TOKEN="legacy-api-token",
    ZENDESK_OAUTH_CLIENT_ID="sumo",
    ZENDESK_OAUTH_CLIENT_SECRET="test-client-secret",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ZendeskOAuthTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.token_requests = []
        self.api_requests = []
        self.token_status = 200
        self.api_status = 200
        clock_patch = patch("time.time", return_value=1_800_000_000)
        self.clock = clock_patch.start()
        self.addCleanup(clock_patch.stop)
        transport_patch = patch("requests.sessions.Session.send", side_effect=self._send)
        transport_patch.start()
        self.addCleanup(transport_patch.stop)

    def _send(self, request, **kwargs):
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = 200
        if request.url.endswith("/oauth/tokens"):
            self.token_requests.append(request)
            response.status_code = self.token_status
            data = {
                "access_token": f"access-token-{len(self.token_requests)}",
                "expires_in": 1800,
                "token_type": "bearer",
            }
        else:
            self.api_requests.append(request)
            response.status_code = self.api_status
            data = (
                {"ticket": {"id": 123, "subject": "Support request"}}
                if self.api_status == 200
                else {"error": "invalid_token"}
            )
        response._content = json.dumps(data).encode()
        return response

    def test_sdk_uses_bearer_authentication_and_reuses_token_across_clients(self):
        self.assertEqual(ZendeskClient().get_ticket(123).subject, "Support request")
        ZendeskClient().get_ticket(123)

        self.assertEqual(len(self.token_requests), 1)
        request = self.token_requests[0]
        self.assertEqual(request.url, "https://oauth-test.zendesk.com/oauth/tokens")
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            json.loads(request.body),
            {
                "grant_type": "client_credentials",
                "client_id": "sumo",
                "client_secret": "test-client-secret",
                "scope": "read users:write tickets:write",
            },
        )
        self.assertEqual(
            [request.headers["Authorization"] for request in self.api_requests],
            ["Bearer access-token-1", "Bearer access-token-1"],
        )

    @override_settings(ZENDESK_OAUTH_CLIENT_ID="", ZENDESK_OAUTH_CLIENT_SECRET="")
    def test_legacy_authentication_when_oauth_is_disabled(self):
        self.assertEqual(ZendeskClient().get_ticket(123).subject, "Support request")

        self.assertEqual(self.token_requests, [])
        scheme, credentials = self.api_requests[0].headers["Authorization"].split()
        self.assertEqual(scheme, "Basic")
        self.assertEqual(
            b64decode(credentials).decode(), "legacy@example.com/token:legacy-api-token"
        )

    def test_partial_oauth_configuration_uses_legacy_authentication(self):
        for missing_setting in ("ZENDESK_OAUTH_CLIENT_ID", "ZENDESK_OAUTH_CLIENT_SECRET"):
            with self.subTest(missing_setting=missing_setting):
                with self.settings(**{missing_setting: ""}):
                    ZendeskClient().get_ticket(123)
                scheme, credentials = self.api_requests[-1].headers["Authorization"].split()
                self.assertEqual(scheme, "Basic")
                self.assertEqual(
                    b64decode(credentials).decode(), "legacy@example.com/token:legacy-api-token"
                )
        self.assertEqual(self.token_requests, [])

    @override_settings(ZENDESK_OAUTH_CLIENT_ID="", ZENDESK_OAUTH_CLIENT_SECRET="")
    def test_incomplete_legacy_credentials_fail_before_any_request(self):
        for missing_setting in (
            "ZENDESK_SUBDOMAIN",
            "ZENDESK_USER_EMAIL",
            "ZENDESK_API_TOKEN",
        ):
            with self.subTest(missing_setting=missing_setting):
                with self.settings(**{missing_setting: ""}):
                    client = ZendeskClient()
                    with self.assertRaises(ZenpyException):
                        client.get_ticket(123)
        self.assertEqual(self.token_requests, [])
        self.assertEqual(self.api_requests, [])

    @override_settings(ZENDESK_SUBDOMAIN="")
    def test_oauth_requires_a_subdomain_before_any_request(self):
        client = ZendeskClient()
        with self.assertRaises(ZenpyException):
            client.get_ticket(123)
        self.assertEqual(self.token_requests, [])
        self.assertEqual(self.api_requests, [])

    def test_oauth_api_rejection_does_not_fall_back_to_legacy(self):
        self.api_status = 401
        with self.assertRaises(APIException):
            ZendeskClient().get_ticket(123)
        self.assertEqual(
            [request.headers["Authorization"] for request in self.api_requests],
            ["Bearer access-token-1"],
        )

    @patch("kitsune.customercare.zendesk.requests.post", side_effect=requests.Timeout)
    def test_oauth_timeout_does_not_fall_back_to_legacy(self, mock_post):
        client = ZendeskClient()
        with self.assertRaises(requests.Timeout):
            client.get_ticket(123)
        self.assertEqual(self.api_requests, [])

    def test_reacquires_token_before_expiry(self):
        ZendeskClient().get_ticket(123)
        self.clock.return_value += 1700
        ZendeskClient().get_ticket(123)
        self.clock.return_value += 99
        ZendeskClient().get_ticket(123)

        self.assertEqual(
            [request.headers["Authorization"] for request in self.api_requests],
            ["Bearer access-token-1", "Bearer access-token-1", "Bearer access-token-2"],
        )

    def test_rotated_secret_does_not_reuse_cached_token(self):
        ZendeskClient().get_ticket(123)
        with self.settings(ZENDESK_OAUTH_CLIENT_SECRET="replacement-secret"):
            ZendeskClient().get_ticket(123)

        self.assertEqual(self.api_requests[-1].headers["Authorization"], "Bearer access-token-2")
        self.assertEqual(
            json.loads(self.token_requests[-1].body)["client_secret"], "replacement-secret"
        )

    def test_other_account_does_not_reuse_cached_token(self):
        ZendeskClient().get_ticket(123)
        with self.settings(ZENDESK_SUBDOMAIN="other-account"):
            ZendeskClient().get_ticket(123)

        self.assertEqual(self.api_requests[-1].headers["Authorization"], "Bearer access-token-2")
        self.assertEqual(
            self.token_requests[-1].url, "https://other-account.zendesk.com/oauth/tokens"
        )

    def test_token_failure_is_lazy_and_not_cached(self):
        self.token_status = 401
        client = ZendeskClient()
        with self.assertRaises(requests.HTTPError):
            client.get_ticket(123)
        self.assertEqual(self.api_requests, [])

        self.token_status = 200
        self.assertEqual(client.get_ticket(123).subject, "Support request")
        self.assertEqual(self.api_requests[-1].headers["Authorization"], "Bearer access-token-2")


class ZendeskConfigurationChecksTests(SimpleTestCase):
    def test_partial_oauth_configuration_warns(self):
        for client_id, client_secret in (("sumo", ""), ("", "secret")):
            with self.subTest(client_id=client_id, client_secret=client_secret):
                with self.settings(
                    ZENDESK_OAUTH_CLIENT_ID=client_id,
                    ZENDESK_OAUTH_CLIENT_SECRET=client_secret,
                ):
                    warnings = check_zendesk_oauth_configuration(None)
                self.assertEqual([warning.id for warning in warnings], ["customercare.W001"])
                self.assertIsInstance(warnings[0], Warning)

    def test_complete_or_disabled_oauth_configuration_is_quiet(self):
        for client_id, client_secret in (("sumo", "secret"), ("", "")):
            with self.subTest(client_id=client_id, client_secret=client_secret):
                with self.settings(
                    ZENDESK_OAUTH_CLIENT_ID=client_id,
                    ZENDESK_OAUTH_CLIENT_SECRET=client_secret,
                ):
                    self.assertEqual(check_zendesk_oauth_configuration(None), [])
