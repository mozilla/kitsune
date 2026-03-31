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
    @patch("django.conf.settings.ZENDESK_SUBDOMAIN", "testsubdomain")
    @patch("django.conf.settings.ZENDESK_USER_EMAIL", "test@example.com")
    @patch("django.conf.settings.ZENDESK_API_TOKEN", "testtoken")
    def test_add_ticket_comment_public(self, mock_zenpy):
        """Test that add_ticket_comment sends a public comment."""
        client = ZendeskClient()
        client.session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        client.session.request.return_value = mock_response

        result = client.add_ticket_comment(123, "Hello there", public=True)

        client.session.request.assert_called_once_with(
            "PUT",
            "https://testsubdomain.zendesk.com/api/v2/tickets/123",
            json={"ticket": {"comment": {"body": "Hello there", "public": True}}},
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_SUBDOMAIN", "testsubdomain")
    @patch("django.conf.settings.ZENDESK_USER_EMAIL", "test@example.com")
    @patch("django.conf.settings.ZENDESK_API_TOKEN", "testtoken")
    def test_add_ticket_comment_private(self, mock_zenpy):
        """Test that add_ticket_comment sends a private comment (internal note)."""
        client = ZendeskClient()
        client.session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        client.session.request.return_value = mock_response

        client.add_ticket_comment(123, "Internal note", public=False)

        client.session.request.assert_called_once_with(
            "PUT",
            "https://testsubdomain.zendesk.com/api/v2/tickets/123",
            json={"ticket": {"comment": {"body": "Internal note", "public": False}}},
        )

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_SUBDOMAIN", "testsubdomain")
    @patch("django.conf.settings.ZENDESK_USER_EMAIL", "test@example.com")
    @patch("django.conf.settings.ZENDESK_API_TOKEN", "testtoken")
    def test_update_ticket_status(self, mock_zenpy):
        """Test that update_ticket_status sends the correct status payload."""
        client = ZendeskClient()
        client.session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        client.session.request.return_value = mock_response

        result = client.update_ticket_status(123, "solved")

        client.session.request.assert_called_once_with(
            "PUT",
            "https://testsubdomain.zendesk.com/api/v2/tickets/123",
            json={"ticket": {"status": "solved"}},
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_update_ticket_status_invalid(self, mock_zenpy):
        """Test that update_ticket_status raises ValueError for invalid status."""
        client = ZendeskClient()
        client.session = Mock()

        with self.assertRaises(ValueError) as ctx:
            client.update_ticket_status(123, "invalid")

        self.assertIn("invalid", str(ctx.exception))
        client.session.request.assert_not_called()

    @patch("kitsune.customercare.zendesk.Zenpy")
    @patch("django.conf.settings.ZENDESK_SUBDOMAIN", "testsubdomain")
    @patch("django.conf.settings.ZENDESK_USER_EMAIL", "test@example.com")
    @patch("django.conf.settings.ZENDESK_API_TOKEN", "testtoken")
    def test_add_ticket_comment_with_user(self, mock_zenpy):
        """Test that add_ticket_comment includes author_id when a user is provided."""
        self.user.profile.zendesk_id = "789"

        client = ZendeskClient()
        client.session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {}
        client.session.request.return_value = mock_response

        client.add_ticket_comment(123, "User comment", user=self.user)

        client.session.request.assert_called_once_with(
            "PUT",
            "https://testsubdomain.zendesk.com/api/v2/tickets/123",
            json={
                "ticket": {"comment": {"body": "User comment", "public": True, "author_id": 789}}
            },
        )

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_with_user_missing_zendesk_id(self, mock_zenpy):
        """Test that add_ticket_comment raises ValueError when user has no zendesk_id."""
        self.user.profile.zendesk_id = ""

        client = ZendeskClient()
        client.session = Mock()

        with self.assertRaises(ValueError) as ctx:
            client.add_ticket_comment(123, "Comment", user=self.user)

        self.assertIn("zendesk_id", str(ctx.exception))
        client.session.request.assert_not_called()

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_add_ticket_comment_with_anonymous_user(self, mock_zenpy):
        """Test that add_ticket_comment raises ValueError for anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        client = ZendeskClient()
        client.session = Mock()

        with self.assertRaises(ValueError) as ctx:
            client.add_ticket_comment(123, "Anon comment", user=AnonymousUser())

        self.assertIn("zendesk_id", str(ctx.exception))
        client.session.request.assert_not_called()
