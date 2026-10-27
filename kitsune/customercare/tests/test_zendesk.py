import json
from base64 import b64decode
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import requests
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group
from django.core.cache import cache
from django.core.checks import Warning
from django.db import ProgrammingError
from django.test import SimpleTestCase, override_settings
from pyquery import PyQuery as pq
from waffle.testutils import override_switch
from zenpy.lib.exception import APIException, RatelimitBudgetExceeded, ZenpyException

from kitsune.customercare.checks import (
    check_zendesk_chat_configuration,
    check_zendesk_chat_switch,
    check_zendesk_oauth_configuration,
)
from kitsune.customercare.models import SupportTicket, ZendeskOrganization, accepted_context_for
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.customercare.utils import send_support_ticket_to_zendesk
from kitsune.customercare.zendesk import (
    ENTERPRISE_SUPPORT_TAG,
    LOGINLESS_TAG,
    ZendeskClient,
    ZendeskProvisioningConflict,
)
from kitsune.flagit.models import FlaggedObject
from kitsune.groups.provisioning import (
    ZendeskProvisioningProgress,
    provision_zendesk_membership,
)
from kitsune.groups.tests import EnterpriseCompanyFactory
from kitsune.products.tests import (
    ProductSupportConfigFactory,
    SupportCoverageFactory,
    ZendeskConfigFactory,
)
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
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

    @patch("kitsune.customercare.zendesk.ZendeskClient.update_user")
    @patch("kitsune.customercare.zendesk.Zenpy")
    @override_settings(ZENDESK_PRODUCT_FIELD_ID=123)
    def test_enterprise_payload_uses_accepted_context_and_origin(self, mock_zenpy, mock_user):
        self.user.profile.zendesk_id = "456"
        mock_user.return_value = Mock(id=456)
        mock_zenpy.return_value.tickets.create.return_value = Mock(ticket=Mock(id=789))
        coverage = SupportCoverageFactory(
            zendesk_config__ticket_form_id="12345",
            zendesk_config__brand_id="42",
            zendesk_product_value="enterprise-firefox",
        )
        ZendeskOrganization.objects.create(
            group_profile=coverage.contract.company, zendesk_id="321"
        )
        self.user.groups.add(coverage.contract.company.group)
        mock_zenpy.return_value.users.organization_memberships.return_value = [
            Mock(user_id=456, organization_id=654, default=True),
            Mock(user_id="00456", organization_id="00321", default=False),
        ]
        ticket = SupportTicketFactory(
            user=self.user,
            product=coverage.product,
            origin=SupportTicket.Origin.ENTERPRISE,
            coverage=coverage,
            org_group=coverage.contract.company,
            accepted_context=accepted_context_for(
                coverage.product, coverage.zendesk_config, coverage
            ),
            zendesk_tags=["seg-rel-esr"],
        )
        coverage.zendesk_config = ZendeskConfigFactory(ticket_form_id="67890", brand_id="99")
        coverage.zendesk_product_value = "changed-product"
        coverage.save()

        self.assertTrue(send_support_ticket_to_zendesk(ticket))

        payload = mock_zenpy.return_value.tickets.create.call_args.args[0]
        self.assertEqual(payload.ticket_form_id, 12345)
        self.assertEqual(payload.brand_id, 42)
        self.assertEqual(payload.organization_id, 321)
        mock_zenpy.return_value.users.organization_memberships.assert_called_once_with(user=456)
        self.assertEqual(mock_zenpy.return_value.organization_memberships.mock_calls, [])
        self.assertIn({"id": 123, "value": "enterprise-firefox"}, payload.custom_fields)
        self.assertEqual(payload.tags, ["seg-rel-esr", ENTERPRISE_SUPPORT_TAG])
        ticket.refresh_from_db()
        self.assertEqual(ticket.zendesk_tags, ["seg-rel-esr"])

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_enterprise_ticket_is_flagged_after_requester_moves_to_another_company(
        self, mock_zenpy
    ):
        coverage = SupportCoverageFactory(contract__company__group__name="Foo")
        company = coverage.contract.company
        ZendeskOrganization.objects.create(group_profile=company, zendesk_id="321")
        self.user.groups.add(company.group)
        ticket = SupportTicketFactory(
            user=self.user,
            product=coverage.product,
            origin=SupportTicket.Origin.ENTERPRISE,
            org_group=company,
            coverage=coverage,
            accepted_context=accepted_context_for(
                coverage.product, coverage.zendesk_config, coverage
            ),
        )
        other_company = EnterpriseCompanyFactory(group__name="Bar")
        ZendeskOrganization.objects.create(group_profile=other_company, zendesk_id="654")
        self.user.groups.set([other_company.group])
        coverage.contract.company = other_company
        coverage.contract.save(update_fields=["company"])

        self.assertFalse(send_support_ticket_to_zendesk(ticket))

        ticket.refresh_from_db()
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)
        self.assertFalse(ticket.zendesk_ticket_id)
        self.assertEqual(ticket.org_group, company)
        self.assertEqual(ticket.accepted_context["company"]["name"], "Foo")
        flag = FlaggedObject.objects.get(object_id=ticket.pk)
        self.assertEqual(flag.reason, FlaggedObject.REASON_OTHER)
        self.assertIn("The requester is no longer a member of the accepted company", flag.notes)
        mock_zenpy.assert_not_called()

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_enterprise_ticket_without_remote_membership_is_flagged(self, mock_zenpy):
        self.user.profile.zendesk_id = "456"
        self.user.profile.save(update_fields=["zendesk_id"])
        mock_zenpy.return_value.users.update.return_value = Mock(id=456)
        coverage = SupportCoverageFactory()
        company = coverage.contract.company
        ZendeskOrganization.objects.create(group_profile=company, zendesk_id="321")
        self.user.groups.add(company.group)
        context = accepted_context_for(coverage.product, coverage.zendesk_config, coverage)
        ticket = SupportTicketFactory(
            user=self.user,
            product=coverage.product,
            origin=SupportTicket.Origin.ENTERPRISE,
            org_group=company,
            coverage=coverage,
            accepted_context=context,
        )
        mock_zenpy.return_value.users.organization_memberships.return_value = []

        self.assertFalse(send_support_ticket_to_zendesk(ticket))

        ticket.refresh_from_db()
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)
        self.assertEqual(ticket.org_group, company)
        self.assertEqual(ticket.accepted_context, context)
        flag = FlaggedObject.objects.get(object_id=ticket.pk)
        self.assertIn(
            "The requester is not a member of the company's Zendesk organization",
            flag.notes,
        )
        mock_zenpy.return_value.tickets.create.assert_not_called()

        moderator = UserFactory(is_superuser=True)
        moderator.groups.add(Group.objects.get_or_create(name=settings.STAFF_GROUP)[0])
        self.client.force_login(moderator)
        spam_ticket = SupportTicketFactory(subject="Spam review")
        moderation_ticket = SupportTicketFactory(subject="Content classification review")
        for other_ticket, reason in (
            (spam_ticket, FlaggedObject.REASON_SPAM),
            (moderation_ticket, FlaggedObject.REASON_CONTENT_MODERATION),
        ):
            FlaggedObject.objects.create(
                content_object=other_ticket, creator=moderator, reason=reason
            )
        queue_url = reverse("flagit.zendesk_spam_queue")

        response = self.client.get(queue_url)

        self.assertContains(response, ticket.subject)
        self.assertIn(flag.notes, pq(response.content)(".notes").text())
        self.assertContains(response, spam_ticket.subject)
        self.assertNotContains(response, moderation_ticket.subject)

        release_url = reverse("flagit.update", args=[flag.pk])
        response = self.client.post(
            release_url, {"status": FlaggedObject.FLAG_REJECTED}, follow=True
        )

        flag.refresh_from_db()
        ticket.refresh_from_db()
        self.assertEqual(flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)
        self.assertContains(response, ticket.subject)
        self.assertIn(flag.notes, pq(response.content)(".notes").text())
        mock_zenpy.return_value.tickets.create.assert_not_called()

        mock_zenpy.return_value.users.organization_memberships.return_value = [
            Mock(user_id=456, organization_id=321)
        ]
        mock_zenpy.return_value.tickets.create.return_value = Mock(ticket=Mock(id=789))

        response = self.client.post(
            release_url, {"status": FlaggedObject.FLAG_REJECTED}, follow=True
        )

        ticket.refresh_from_db()
        flag.refresh_from_db()
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_SENT)
        self.assertEqual(ticket.zendesk_ticket_id, "789")
        self.assertEqual(ticket.org_group, company)
        self.assertEqual(ticket.accepted_context, context)
        self.assertEqual(flag.status, FlaggedObject.FLAG_REJECTED)
        self.assertNotContains(response, ticket.subject)
        self.assertContains(response, spam_ticket.subject)
        self.assertNotContains(response, moderation_ticket.subject)
        payload = mock_zenpy.return_value.tickets.create.call_args.args[0]
        self.assertEqual(payload.organization_id, 321)
        self.assertEqual(mock_zenpy.return_value.organization_memberships.mock_calls, [])

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_enterprise_ticket_without_linked_organization_is_flagged(self, mock_zenpy):
        for mapping_state in ("missing", None, ""):
            with self.subTest(mapping_state=mapping_state):
                coverage = SupportCoverageFactory()
                organization = ZendeskOrganization.objects.create(
                    group_profile=coverage.contract.company,
                    zendesk_id="321" if mapping_state == "missing" else mapping_state,
                )
                ticket = SupportTicketFactory(
                    user=self.user,
                    product=coverage.product,
                    origin=SupportTicket.Origin.ENTERPRISE,
                    coverage=coverage,
                    org_group=coverage.contract.company,
                    accepted_context=accepted_context_for(
                        coverage.product, coverage.zendesk_config, coverage
                    ),
                )
                if mapping_state == "missing":
                    organization.delete()

                self.assertFalse(send_support_ticket_to_zendesk(ticket))

                ticket.refresh_from_db()
                self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)
                self.assertFalse(ticket.zendesk_ticket_id)
                flag = FlaggedObject.objects.get(object_id=ticket.pk)
                self.assertEqual(flag.reason, FlaggedObject.REASON_OTHER)
                self.assertIn("The company has no linked Zendesk organization", flag.notes)
        mock_zenpy.assert_not_called()

    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_product_ticket_does_not_set_or_read_organization(self, mock_zenpy):
        self.user.profile.zendesk_id = "456"
        mock_zenpy.return_value.users.update.return_value = Mock(id=456, organization_id=654)
        mock_zenpy.return_value.tickets.create.return_value = Mock(ticket=Mock(id=789))
        support_config = ProductSupportConfigFactory(zendesk_config=ZendeskConfigFactory())
        ticket = SupportTicketFactory(
            user=self.user,
            product=support_config.product,
            origin=SupportTicket.Origin.PRODUCT,
            zendesk_tags=["seg-rel-esr", ENTERPRISE_SUPPORT_TAG],
            accepted_context=accepted_context_for(
                support_config.product, support_config.zendesk_config
            ),
        )

        self.assertTrue(send_support_ticket_to_zendesk(ticket))

        payload = mock_zenpy.return_value.tickets.create.call_args.args[0]
        self.assertIsNone(payload.organization_id)
        self.assertEqual(payload.tags, ["seg-rel-esr"])
        mock_zenpy.return_value.users.organization_memberships.assert_not_called()
        self.assertEqual(mock_zenpy.return_value.organization_memberships.mock_calls, [])

    @patch("kitsune.customercare.zendesk.ZendeskClient.create_user")
    @patch("kitsune.customercare.zendesk.Zenpy")
    def test_enterprise_ticket_of_a_deleted_submitter_is_held_for_review(
        self, mock_zenpy, mock_create_user
    ):
        coverage = SupportCoverageFactory()
        ZendeskOrganization.objects.create(
            group_profile=coverage.contract.company, zendesk_id="321"
        )
        ticket = SupportTicketFactory(
            user=self.user,
            product=coverage.product,
            category="deployment",
            origin=SupportTicket.Origin.ENTERPRISE,
            coverage=coverage,
            org_group=coverage.contract.company,
            accepted_context=accepted_context_for(
                coverage.product, coverage.zendesk_config, coverage
            ),
        )
        self.user.delete()
        ticket.refresh_from_db()

        self.assertFalse(send_support_ticket_to_zendesk(ticket))

        ticket.refresh_from_db()
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)
        self.assertIn(
            "The requester is no longer a member of the accepted company",
            FlaggedObject.objects.get(object_id=ticket.pk).notes,
        )
        mock_create_user.assert_not_called()
        mock_zenpy.assert_not_called()

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
        self.api_error = "invalid_token"
        self.api_headers = {}
        self.api_exception = None
        self.api_timeouts = []
        self.organization_data = {"id": 123, "name": "Existing company"}
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
            self.api_timeouts.append(kwargs.get("timeout"))
            if self.api_exception is not None:
                raise self.api_exception
            response.status_code = self.api_status
            response.headers.update(self.api_headers)
            if self.api_status != 200:
                data = {"error": self.api_error}
            elif "/organizations/" in request.url:
                data = {"organization": self.organization_data}
            else:
                data = {"ticket": {"id": 123, "subject": "Support request"}}
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
                "scope": "read users:write tickets:write organizations:write",
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

    def test_changed_scopes_do_not_reuse_a_narrower_cached_token(self):
        with patch("kitsune.customercare.zendesk.OAUTH_SCOPES", "read users:write tickets:write"):
            ZendeskClient().get_ticket(123)
        ZendeskClient().get_ticket(123)

        self.assertEqual(
            [request.headers["Authorization"] for request in self.api_requests],
            ["Bearer access-token-1", "Bearer access-token-2"],
        )
        self.assertEqual(
            json.loads(self.token_requests[-1].body)["scope"],
            "read users:write tickets:write organizations:write",
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

    @override_settings(ZENDESK_SYNC_TIMEOUT=7)
    def test_organization_link_uses_a_fresh_canonical_id_without_remote_writes(self):
        client = ZendeskClient(disable_cache=True, ratelimit_budget=0)
        self.assertEqual(client.validate_organization("00123"), "123")
        self.api_status = 404
        self.api_error = "RecordNotFound"

        with self.assertRaises(ZendeskProvisioningConflict) as error:
            client.validate_organization("123")

        self.assertEqual(error.exception.code, "resource_missing")
        self.assertEqual(
            [(request.method, request.url) for request in self.api_requests],
            [
                ("GET", "https://oauth-test.zendesk.com/api/v2/organizations/123.json"),
                ("GET", "https://oauth-test.zendesk.com/api/v2/organizations/123.json"),
            ],
        )
        self.assertEqual(self.api_timeouts, [7, 7])

    def test_invalid_organization_id_fails_before_any_request(self):
        for organization_id in ("", "0", "-1", "+123", "1.5", "１２３", "123/456", "1" * 256):
            with self.subTest(organization_id=organization_id):
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    ZendeskClient().validate_organization(organization_id)
                self.assertEqual(error.exception.code, "zendesk_conflict")
        self.assertEqual(self.token_requests, [])
        self.assertEqual(self.api_requests, [])

    def test_missing_organization_is_a_safe_permanent_conflict(self):
        self.api_status = 404
        for api_error in ("RecordNotFound", "NotFound"):
            with self.subTest(api_error=api_error):
                self.api_error = api_error
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    ZendeskClient(disable_cache=True).validate_organization("123")
                self.assertEqual(error.exception.code, "resource_missing")
                self.assertNotIn(api_error, str(error.exception))

    def test_organization_api_failures_are_classified(self):
        for status in (400, 409, 422):
            with self.subTest(status=status):
                self.api_status = status
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    ZendeskClient(disable_cache=True).validate_organization("123")
                self.assertEqual(error.exception.code, "zendesk_conflict")
        for status in (401, 403, 503):
            with self.subTest(status=status):
                self.api_status = status
                with self.assertRaises(APIException) as error:
                    ZendeskClient(disable_cache=True).validate_organization("123")
                self.assertEqual(error.exception.response.status_code, status)

    def test_organization_timeout_propagates_without_a_mapping(self):
        self.api_exception = requests.Timeout("Provider request timed out")
        with self.assertRaises(requests.Timeout):
            ZendeskClient(disable_cache=True).validate_organization("123")

    @patch("zenpy.lib.api.sleep")
    def test_organization_rate_limit_exits_without_sleep(self, sleep):
        self.api_status = 429
        self.api_headers = {"Retry-After": "60"}
        with self.assertRaises(RatelimitBudgetExceeded):
            ZendeskClient(disable_cache=True, ratelimit_budget=0).validate_organization("123")
        sleep.assert_not_called()
        self.assertEqual(len(self.api_requests), 1)


class ZendeskProvisioningTransportMixin:
    """Exercise real Zenpy provisioning requests with no network access."""

    def setUp(self):
        super().setUp()
        self.responses = []
        self.requests = []
        transport = patch("requests.sessions.Session.send", side_effect=self.send)
        transport.start()
        self.addCleanup(transport.stop)
        self.addCleanup(lambda: self.assertEqual(self.responses, []))
        self.client = ZendeskClient(disable_cache=True, ratelimit_budget=0)
        self.user_args = {"email": "member@example.com", "name": "Invited Name", "locale": "fr"}
        self.organization_args = {
            "name": "Invited Company",
            "external_id": "c1e9f574-00d8-4a32-b84b-b1f33a9ce149",
        }

    def expect(self, method, path, data, status=200):
        self.responses.append((method, path, data, status))

    def send(self, request, **kwargs):
        self.requests.append(request)
        self.assertTrue(self.responses, f"Unexpected request: {request.method} {request.url}")
        method, path, data, status = self.responses.pop(0)
        url = urlsplit(request.url)
        self.assertEqual(url.netloc, "provisioning-test.zendesk.com")
        self.assertEqual((request.method, url.path), (method, f"/api/v2/{path}.json"))
        if isinstance(data, requests.RequestException):
            raise data
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = status
        response._content = b"" if status == 204 else json.dumps(data).encode()
        return response

    def remote_user(self, **fields):
        return {
            "id": 123,
            "name": "Established Remote Name",
            "email": "member@example.com",
            "locale": "en-US",
            "role": "end-user",
            "active": True,
            "suspended": False,
            "shared": False,
            "external_id": None,
            "user_fields": {},
            **fields,
        }

    def expect_users(self, *users):
        self.expect(
            "GET", "users/search", {"users": list(users), "count": len(users), "next_page": None}
        )

    def expect_memberships(self, *organization_ids, next_page=None, default_organization_id=None):
        self.expect(
            "GET",
            "users/123/organization_memberships",
            {
                "organization_memberships": [
                    {
                        "id": index + 1,
                        "user_id": 123,
                        "organization_id": organization_id,
                        "default": organization_id == default_organization_id,
                    }
                    for index, organization_id in enumerate(organization_ids)
                ],
                "next_page": next_page,
            },
        )


@override_settings(
    ZENDESK_SUBDOMAIN="provisioning-test",
    ZENDESK_USER_EMAIL="provisioner@example.com",
    ZENDESK_API_TOKEN="test-api-token",
    ZENDESK_OAUTH_CLIENT_ID="",
    ZENDESK_OAUTH_CLIENT_SECRET="",
)
class ZendeskProvisioningTests(ZendeskProvisioningTransportMixin, SimpleTestCase):
    def test_conflict_exposes_only_safe_codes(self):
        for code, expected in (
            ("account_conflict", "account_conflict"),
            ("company_conflict", "company_conflict"),
            ("resource_missing", "resource_missing"),
            ("zendesk_conflict", "zendesk_conflict"),
            ("Provider response with private details", "zendesk_conflict"),
            (None, "zendesk_conflict"),
        ):
            with self.subTest(code=code):
                error = ZendeskProvisioningConflict(code)
                self.assertEqual(error.code, expected)
                self.assertEqual(str(error), expected)

    def test_saved_organization_preserves_name_identity_and_sharing_policy(self):
        organization = {
            "id": 456,
            "name": "Established Company",
            "external_id": "managed-elsewhere",
            "shared_comments": True,
            "shared_tickets": True,
        }
        self.expect("GET", "organizations/456", {"organization": organization})

        self.assertEqual(
            self.client.ensure_organization(**self.organization_args, zendesk_id="00456"), "456"
        )

    def test_organization_lost_response_reuses_stable_uuid_not_name_search(self):
        self.expect("POST", "organizations/create_or_update", requests.Timeout("Lost response"))
        with self.assertRaises(requests.Timeout):
            self.client.ensure_organization(**self.organization_args)
        self.expect(
            "POST",
            "organizations/create_or_update",
            {"organization": {"id": 456, **self.organization_args}},
        )

        self.assertEqual(
            self.client.ensure_organization(**self.organization_args, zendesk_id=""), "456"
        )
        for request in self.requests:
            organization = json.loads(request.body)["organization"]
            self.assertEqual(organization["external_id"], self.organization_args["external_id"])
            self.assertEqual(organization["name"], self.organization_args["name"])
            self.assertNotIn("shared_comments", organization)
            self.assertNotIn("shared_tickets", organization)

    def test_organization_name_collision_is_not_adopted(self):
        self.expect(
            "POST",
            "organizations/create_or_update",
            {"error": "RecordInvalid", "description": "Name already exists"},
            status=422,
        )
        self.expect(
            "GET",
            "organizations/show_many",
            {
                "organizations": [
                    {"id": 789, "name": self.organization_args["name"], "external_id": "other"}
                ],
                "next_page": None,
            },
        )
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_organization(**self.organization_args)
        self.assertEqual(error.exception.code, "zendesk_conflict")
        self.assertNotIn("Name already exists", str(error.exception))

    def test_organization_422_recovers_only_by_matching_external_id(self):
        for external_id in (
            self.organization_args["external_id"],
            self.organization_args["external_id"].upper(),
        ):
            with self.subTest(external_id=external_id):
                self.expect(
                    "POST",
                    "organizations/create_or_update",
                    {"error": "RecordInvalid"},
                    status=422,
                )
                self.expect(
                    "GET",
                    "organizations/show_many",
                    {
                        "organizations": [
                            {"id": 789, "external_id": "another-company"},
                            {"id": "00456", "external_id": external_id},
                        ],
                        "next_page": None,
                    },
                )

                self.assertEqual(self.client.ensure_organization(**self.organization_args), "456")

                self.assertEqual(
                    json.loads(self.requests[-2].body),
                    {"organization": self.organization_args},
                )
                self.assertEqual(
                    parse_qs(urlsplit(self.requests[-1].url).query),
                    {"external_ids": [self.organization_args["external_id"]]},
                )
                self.assertIsNone(self.requests[-1].body)

    def test_organization_422_without_matching_external_id_is_a_safe_conflict(self):
        for organizations in (
            [],
            [{"id": 789, "external_id": "another-company"}],
            [{"id": 456, "external_id": None}],
        ):
            with self.subTest(organizations=organizations):
                self.expect(
                    "POST",
                    "organizations/create_or_update",
                    {"error": "RecordInvalid", "description": "Private provider details"},
                    status=422,
                )
                self.expect(
                    "GET",
                    "organizations/show_many",
                    {"organizations": organizations, "next_page": None},
                )

                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.ensure_organization(**self.organization_args)

                self.assertEqual(error.exception.code, "zendesk_conflict")
                self.assertNotIn("Private provider details", str(error.exception))

    def test_organization_422_lookup_preserves_error_translation(self):
        for status, code in (
            (400, "zendesk_conflict"),
            (404, "resource_missing"),
            (409, "zendesk_conflict"),
            (422, "zendesk_conflict"),
            (401, None),
            (403, None),
            (503, None),
        ):
            with self.subTest(status=status):
                self.expect(
                    "POST",
                    "organizations/create_or_update",
                    {"error": "RecordInvalid"},
                    status=422,
                )
                self.expect(
                    "GET",
                    "organizations/show_many",
                    {"error": "ProviderFailure", "description": "Private provider details"},
                    status=status,
                )
                exception = ZendeskProvisioningConflict if code else APIException

                with self.assertRaises(exception) as error:
                    self.client.ensure_organization(**self.organization_args)

                if code:
                    self.assertEqual(error.exception.code, code)
                    self.assertNotIn("Private provider details", str(error.exception))
                else:
                    self.assertEqual(error.exception.response.status_code, status)

    def test_organization_other_conflicts_do_not_trigger_identity_lookup(self):
        for status in (400, 409):
            with self.subTest(status=status):
                self.expect(
                    "POST",
                    "organizations/create_or_update",
                    {"error": "RecordInvalid"},
                    status=status,
                )

                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.ensure_organization(**self.organization_args)

                self.assertEqual(error.exception.code, "zendesk_conflict")

    def test_missing_saved_organization_does_not_fall_back_to_creation(self):
        self.expect("GET", "organizations/456", {"error": "RecordNotFound"}, status=404)
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_organization(**self.organization_args, zendesk_id="456")
        self.assertEqual(error.exception.code, "resource_missing")

    def test_organization_requires_stable_external_id(self):
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_organization(name="Company", external_id="")
        self.assertEqual(error.exception.code, "zendesk_conflict")

    def test_organization_rejects_mismatching_upsert_identity(self):
        self.expect(
            "POST",
            "organizations/create_or_update",
            {"organization": {"id": 456, "external_id": "another-company"}},
        )
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_organization(**self.organization_args)
        self.assertEqual(error.exception.code, "zendesk_conflict")

    def test_prepared_user_creation_suppresses_email_without_fabricating_identity(self):
        self.expect_users()
        self.expect("POST", "users", {"user": self.remote_user()}, status=201)

        self.assertEqual(self.client.ensure_user(**self.user_args), "123")

        user = json.loads(self.requests[-1].body)["user"]
        self.assertEqual(user["email"], self.user_args["email"])
        self.assertEqual(user["role"], "end-user")
        self.assertFalse(user["verified"])
        self.assertTrue(user["skip_verify_email"])
        self.assertNotIn("external_id", user)
        self.assertNotIn("user_fields", user)
        self.assertNotIn("organization_id", user)

    def test_real_fxa_identity_is_included_only_for_new_users(self):
        self.expect_users()
        self.expect(
            "POST",
            "users",
            {"user": self.remote_user(external_id="fxa-uid", user_fields={"user_id": "fxa-uid"})},
            status=201,
        )

        self.assertEqual(self.client.ensure_user(**self.user_args, fxa_uid="fxa-uid"), "123")

        user = json.loads(self.requests[-1].body)["user"]
        self.assertEqual(user["external_id"], "fxa-uid")
        self.assertEqual(user["user_fields"], {"user_id": "fxa-uid"})
        self.assertTrue(user["verified"])
        self.assertTrue(user["skip_verify_email"])

    def test_existing_user_preserves_name_email_locale_and_remote_identity(self):
        user = self.remote_user(
            email="Member@Example.com",
            external_id="fxa-uid",
            user_fields={"user_id": "fxa-uid", "unrelated": "preserved"},
        )
        for saved_id in (None, "00123"):
            with self.subTest(saved_id=saved_id):
                if saved_id is None:
                    self.expect_users(user)
                else:
                    self.expect("GET", "users/123", {"user": user})
                self.assertEqual(
                    self.client.ensure_user(
                        **self.user_args, fxa_uid="fxa-uid", zendesk_id=saved_id
                    ),
                    "123",
                )

    def test_email_lookup_quotes_search_metacharacters(self):
        email = '"member\\name"@example.com'
        self.expect_users(self.remote_user(email=email))

        self.assertEqual(self.client.ensure_user(**{**self.user_args, "email": email}), "123")
        self.assertEqual(
            parse_qs(urlsplit(self.requests[-1].url).query),
            {"query": ['email:"\\"member\\\\name\\"@example.com"']},
        )

    def test_existing_email_without_fxa_identity_is_not_updated(self):
        self.expect_users(self.remote_user())

        self.assertEqual(self.client.ensure_user(**self.user_args, fxa_uid="fxa-uid"), "123")

    def test_prepared_user_does_not_claim_unmatched_remote_identity(self):
        for fields in (
            {"external_id": "unknown-fxa-uid"},
            {"user_fields": {"user_id": "unknown-fxa-uid"}},
        ):
            with self.subTest(fields=fields):
                self.expect_users(self.remote_user(**fields))
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.ensure_user(**self.user_args)
                self.assertEqual(error.exception.code, "account_conflict")

    def test_matching_external_id_does_not_override_conflicting_custom_fxa_identity(self):
        self.expect_users(
            self.remote_user(external_id="fxa-uid", user_fields={"user_id": "different-fxa-uid"})
        )
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_user(**self.user_args, fxa_uid="fxa-uid")
        self.assertEqual(error.exception.code, "account_conflict")

    def test_existing_remote_identity_must_match_local_fxa_identity(self):
        self.expect_users(self.remote_user(external_id="different-fxa-uid"))
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_user(**self.user_args, fxa_uid="fxa-uid")
        self.assertEqual(error.exception.code, "account_conflict")

    def test_saved_user_conflict_requires_manual_correction(self):
        for fields in (
            {"id": 789},
            {"email": "another-member@example.com"},
            {"external_id": "another-fxa-uid"},
        ):
            with self.subTest(fields=fields):
                self.expect("GET", "users/123", {"user": self.remote_user(**fields)})
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.ensure_user(**self.user_args, fxa_uid="fxa-uid", zendesk_id="123")
                self.assertEqual(error.exception.code, "account_conflict")

    def test_ambiguous_email_results_are_not_linked(self):
        self.expect_users(self.remote_user(), self.remote_user(id=789))
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_user(**self.user_args)
        self.assertEqual(error.exception.code, "account_conflict")

    def test_secondary_or_partial_email_match_is_not_adopted(self):
        self.expect_users(self.remote_user(email="other-member@example.com"))
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_user(**self.user_args)
        self.assertEqual(error.exception.code, "account_conflict")

    def test_deleted_suspended_shared_and_privileged_users_are_rejected(self):
        for fields in (
            {"active": False},
            {"active": None},
            {"active": 1},
            {"suspended": True},
            {"shared": True},
            {"shared_agent": True},
            {"chat_only": True},
            {"role": "agent"},
            {"role": "admin"},
            {"role": None},
            {"custom_role_id": 321},
        ):
            with self.subTest(fields=fields):
                self.expect_users(self.remote_user(**fields))
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.ensure_user(**self.user_args)
                self.assertEqual(error.exception.code, "account_conflict")

    def test_missing_saved_user_is_not_recreated(self):
        self.expect("GET", "users/123", {"error": "RecordNotFound"}, status=404)
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.client.ensure_user(**self.user_args, zendesk_id="123")
        self.assertEqual(error.exception.code, "resource_missing")

    def test_removal_user_allows_activity_and_identity_drift_without_mutation(self):
        for fields in (
            {},
            {"active": False},
            {"active": None},
            {"suspended": True},
            {"email": "changed@example.com"},
            {"email": None},
            {"external_id": "another-fxa-uid"},
            {"user_fields": {"user_id": "another-fxa-uid"}},
            {
                "active": False,
                "suspended": True,
                "email": "changed@example.com",
                "external_id": "another-fxa-uid",
                "user_fields": {"user_id": "different-fxa-uid"},
            },
        ):
            with self.subTest(fields=fields):
                self.expect("GET", "users/123", {"user": self.remote_user(**fields)})

                self.assertEqual(self.client.validate_removal_user("00123"), "123")

                self.assertEqual(urlsplit(self.requests[-1].url).query, "")
                self.assertIsNone(self.requests[-1].body)
        self.assertTrue(all(request.method == "GET" for request in self.requests))

    def test_removal_user_does_not_require_activity_or_identity_fields(self):
        self.expect("GET", "users/123", {"user": {"id": "00123", "role": "end-user"}})

        self.assertEqual(self.client.validate_removal_user("123"), "123")

    def test_removal_user_rejects_mismatched_shared_or_privileged_accounts(self):
        for fields in (
            {"id": 789},
            {"role": "agent"},
            {"role": "admin"},
            {"role": None},
            {"shared": True},
            {"shared_agent": True},
            {"chat_only": True},
            {"custom_role_id": 321},
        ):
            with self.subTest(fields=fields):
                self.expect("GET", "users/123", {"user": self.remote_user(**fields)})

                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.validate_removal_user("123")

                self.assertEqual(error.exception.code, "account_conflict")

    def test_removal_user_rejects_malformed_saved_ids_without_provider_requests(self):
        for invalid_id in (None, True, "", "0", "-1", "１２３", "123/456", "1" * 256):
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.validate_removal_user(invalid_id)

                self.assertEqual(error.exception.code, "zendesk_conflict")
        self.assertEqual(self.requests, [])

    def test_removal_user_preserves_provider_error_translation(self):
        for status, code in (
            (400, "zendesk_conflict"),
            (404, "resource_missing"),
            (409, "zendesk_conflict"),
            (422, "zendesk_conflict"),
            (401, None),
            (403, None),
            (503, None),
        ):
            with self.subTest(status=status):
                self.expect(
                    "GET",
                    "users/123",
                    {"error": "ProviderFailure", "description": "Private provider details"},
                    status=status,
                )
                exception = ZendeskProvisioningConflict if code else APIException

                with self.assertRaises(exception) as error:
                    self.client.validate_removal_user("123")

                if code:
                    self.assertEqual(error.exception.code, code)
                    self.assertNotIn("Private provider details", str(error.exception))
                else:
                    self.assertEqual(error.exception.response.status_code, status)

    def test_user_lost_response_manual_retry_preserves_created_user(self):
        self.expect_users()
        self.expect("POST", "users", requests.Timeout("Lost response"))
        with self.assertRaises(requests.Timeout):
            self.client.ensure_user(**self.user_args)
        self.expect_users(self.remote_user())

        self.assertEqual(self.client.ensure_user(**self.user_args), "123")

    def test_user_creation_conflict_requires_manual_retry(self):
        for status in (400, 409, 422):
            with self.subTest(status=status):
                self.expect_users()
                self.expect("POST", "users", {"error": "RecordInvalid"}, status=status)
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.ensure_user(**self.user_args)
                self.assertEqual(error.exception.code, "zendesk_conflict")

                self.expect_users(self.remote_user(name="Concurrent Creator's Name"))
                self.assertEqual(self.client.ensure_user(**self.user_args), "123")

    def test_membership_creation_uses_only_dedicated_endpoint(self):
        self.expect_memberships(789, default_organization_id=789)
        self.expect(
            "POST",
            "organization_memberships",
            {"organization_membership": {"id": 789, "user_id": 123, "organization_id": 456}},
            status=201,
        )

        self.client.ensure_organization_membership(user_id="00123", organization_id="00456")
        membership = json.loads(self.requests[-1].body)["organization_membership"]
        self.assertEqual(membership["user_id"], 123)
        self.assertEqual(membership["organization_id"], 456)
        self.assertNotIn("default", membership)

    def test_membership_convergence_repeats_without_writes(self):
        for _ in range(2):
            self.expect_memberships(456, 890, default_organization_id=890)
            self.client.ensure_organization_membership(user_id="00123", organization_id="00456")
            self.expect_memberships(456, 890, default_organization_id=890)
            self.client.remove_organization_memberships(
                user_id="00123", organization_ids={"00789"}
            )
        self.assertEqual([request.method for request in self.requests], ["GET"] * 4)

    def test_membership_snapshot_is_fully_read_once_before_removal_and_creation(self):
        self.expect_memberships(
            789,
            default_organization_id=789,
            next_page=(
                "https://provisioning-test.zendesk.com/api/v2/"
                "users/123/organization_memberships.json?page=2"
            ),
        )
        self.expect(
            "GET",
            "users/123/organization_memberships",
            {
                "organization_memberships": [{"id": 2, "user_id": 123, "organization_id": 890}],
                "next_page": None,
            },
        )
        self.expect("DELETE", "organization_memberships/1", None, status=204)
        self.expect(
            "POST",
            "organization_memberships",
            {"organization_membership": {"id": 3, "user_id": 123, "organization_id": 456}},
            status=201,
        )

        memberships = self.client.get_organization_memberships(user_id="00123")

        self.assertIsInstance(memberships, list)
        self.assertEqual([membership.organization_id for membership in memberships], [789, 890])
        self.assertEqual([request.method for request in self.requests], ["GET", "GET"])
        self.assertEqual(parse_qs(urlsplit(self.requests[1].url).query), {"page": ["2"]})
        self.client.remove_organization_memberships(
            user_id="00123", organization_ids={"00789"}, memberships=memberships
        )
        self.client.ensure_organization_membership(
            user_id="00123", organization_id="00456", memberships=memberships
        )

        self.assertEqual(
            [request.method for request in self.requests], ["GET", "GET", "DELETE", "POST"]
        )

    def test_existing_membership_snapshot_needs_no_writes_or_extra_reads(self):
        self.expect_memberships(456, 890, default_organization_id=890)
        memberships = self.client.get_organization_memberships(user_id="00123")
        self.client.remove_organization_memberships(
            user_id="00123", organization_ids={"00789"}, memberships=memberships
        )
        self.client.ensure_organization_membership(
            user_id="00123", organization_id="00456", memberships=memberships
        )

        self.assertEqual([request.method for request in self.requests], ["GET"])

    def test_empty_membership_snapshot_does_not_trigger_another_read(self):
        self.expect_memberships()
        self.expect(
            "POST",
            "organization_memberships",
            {"organization_membership": {"id": 1, "user_id": 123, "organization_id": 456}},
            status=201,
        )

        memberships = self.client.get_organization_memberships(user_id="123")
        self.client.remove_organization_memberships(
            user_id="123", organization_ids={"789"}, memberships=memberships
        )
        self.client.ensure_organization_membership(
            user_id="123", organization_id="456", memberships=memberships
        )

        self.assertEqual([request.method for request in self.requests], ["GET", "POST"])

    def test_existing_membership_on_later_page_does_not_create(self):
        self.expect_memberships(
            789,
            default_organization_id=789,
            next_page=(
                "https://provisioning-test.zendesk.com/api/v2/"
                "users/123/organization_memberships.json?page=2"
            ),
        )
        self.expect_memberships(456)

        self.client.ensure_organization_membership(user_id="123", organization_id="456")

        self.assertEqual(parse_qs(urlsplit(self.requests[-1].url).query), {"page": ["2"]})
        self.assertEqual([request.method for request in self.requests], ["GET", "GET"])

    def test_membership_removal_selects_canonical_organizations(self):
        self.expect_memberships(789, 456, 890, 999, default_organization_id=789)
        for membership_id in (2, 3):
            self.expect("DELETE", f"organization_memberships/{membership_id}", None, status=204)

        self.client.remove_organization_memberships(
            user_id="00123", organization_ids=iter(("00456", "00890"))
        )

        for request, membership_id in zip(self.requests[1:], (2, 3), strict=True):
            self.assertEqual(
                json.loads(request.body), {"organization_membership": {"id": membership_id}}
            )
            self.assertEqual(urlsplit(request.url).query, "")

    def test_membership_removal_with_nothing_selected_only_reads(self):
        for organizations, organization_ids in (
            ((), []),
            ((456,), []),
            ((456,), ["789"]),
        ):
            with self.subTest(organizations=organizations, organization_ids=organization_ids):
                self.expect_memberships(*organizations)
                self.client.remove_organization_memberships(
                    user_id="123", organization_ids=organization_ids
                )
        self.assertTrue(all(request.method == "GET" for request in self.requests))

    def test_empty_membership_removal_selection_reuses_supplied_snapshot(self):
        self.expect_memberships(456, 890, default_organization_id=890)
        memberships = self.client.get_organization_memberships(user_id="123")

        self.client.remove_organization_memberships(
            user_id="123", organization_ids=[], memberships=memberships
        )

        self.assertEqual([request.method for request in self.requests], ["GET"])

    def test_membership_removal_finishes_pagination_before_deleting(self):
        self.expect_memberships(
            789,
            456,
            next_page=(
                "https://provisioning-test.zendesk.com/api/v2/"
                "users/123/organization_memberships.json?page=2"
            ),
        )
        self.expect(
            "GET",
            "users/123/organization_memberships",
            {
                "organization_memberships": [{"id": 3, "user_id": 123, "organization_id": 890}],
                "next_page": None,
            },
        )
        self.expect("DELETE", "organization_memberships/1", None, status=204)
        self.expect("DELETE", "organization_memberships/3", None, status=204)

        self.client.remove_organization_memberships(user_id="123", organization_ids={"789", "890"})

        self.assertEqual(parse_qs(urlsplit(self.requests[1].url).query), {"page": ["2"]})

    def test_membership_removal_continues_after_concurrent_deletion(self):
        response = requests.Response()
        response.status_code = 404
        for error in (
            {"error": "RecordNotFound"},
            {"error": "Membership already removed"},
            requests.HTTPError(response=response),
        ):
            for use_snapshot in (False, True):
                with self.subTest(error=error, use_snapshot=use_snapshot):
                    self.expect_memberships(789, 456, 890)
                    snapshot = (
                        {"memberships": self.client.get_organization_memberships(user_id="123")}
                        if use_snapshot
                        else {}
                    )
                    self.expect("DELETE", "organization_memberships/1", error, status=404)
                    self.expect("DELETE", "organization_memberships/3", None, status=204)

                    self.client.remove_organization_memberships(
                        user_id="123", organization_ids={"789", "890"}, **snapshot
                    )

    def test_membership_removal_missing_list_remains_a_conflict(self):
        response = requests.Response()
        response.status_code = 404
        for error in (
            {"error": "RecordNotFound"},
            {"error": "Private provider details"},
            requests.HTTPError(response=response),
        ):
            with self.subTest(error=error):
                self.expect("GET", "users/123/organization_memberships", error, status=404)

                with self.assertRaises(ZendeskProvisioningConflict) as raised:
                    self.client.remove_organization_memberships(
                        user_id="123", organization_ids={"789"}
                    )
                self.assertEqual(raised.exception.code, "resource_missing")

    def test_membership_removal_translates_provider_errors_without_hiding_transient_errors(self):
        for method, path in (
            ("GET", "users/123/organization_memberships"),
            ("DELETE", "organization_memberships/1"),
        ):
            for status, code in (
                (400, "zendesk_conflict"),
                (409, "zendesk_conflict"),
                (422, "zendesk_conflict"),
                (401, None),
                (403, None),
                (503, None),
            ):
                with self.subTest(method=method, status=status):
                    if method == "DELETE":
                        self.expect_memberships(456)
                    self.expect(method, path, {"error": "Private provider details"}, status=status)
                    exception = ZendeskProvisioningConflict if code else APIException
                    with self.assertRaises(exception) as error:
                        self.client.remove_organization_memberships(
                            user_id="123", organization_ids=["456"]
                        )
                    if code:
                        self.assertEqual(error.exception.code, code)
                        self.assertNotIn("Private provider details", str(error.exception))
                    else:
                        self.assertEqual(error.exception.response.status_code, status)

    def test_membership_response_must_match_requested_pair(self):
        for pair in (
            {"user_id": 789, "organization_id": 456},
            {"user_id": 123, "organization_id": 789},
            {"user_id": None, "organization_id": 456},
        ):
            with self.subTest(pair=pair):
                self.expect_memberships()
                self.expect(
                    "POST",
                    "organization_memberships",
                    {"organization_membership": {"id": 891, **pair}},
                    status=201,
                )
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.client.ensure_organization_membership(
                        user_id="123", organization_id="456"
                    )
                self.assertEqual(error.exception.code, "zendesk_conflict")

    def test_membership_422_finds_target_after_unrelated_default_on_earlier_page(self):
        for use_snapshot in (False, True):
            with self.subTest(use_snapshot=use_snapshot):
                start = len(self.requests)
                self.expect_memberships(789, default_organization_id=789)
                snapshot = (
                    {"memberships": self.client.get_organization_memberships(user_id="123")}
                    if use_snapshot
                    else {}
                )
                self.expect(
                    "POST", "organization_memberships", {"error": "RecordInvalid"}, status=422
                )
                self.expect_memberships(
                    789,
                    default_organization_id=789,
                    next_page=(
                        "https://provisioning-test.zendesk.com/api/v2/"
                        "users/123/organization_memberships.json?page=2"
                    ),
                )
                self.expect_memberships(456)

                self.client.ensure_organization_membership(
                    user_id="123", organization_id="456", **snapshot
                )

                self.assertEqual(
                    [request.method for request in self.requests[start:]],
                    ["GET", "POST", "GET", "GET"],
                )

    def test_membership_422_is_success_when_a_fresh_read_finds_the_target(self):
        for organizations in ((456,), (789, 456), (456, 789)):
            with self.subTest(organizations=organizations):
                self.expect_memberships()
                self.expect(
                    "POST", "organization_memberships", {"error": "RecordInvalid"}, status=422
                )
                self.expect_memberships(*organizations, default_organization_id=789)

                self.client.ensure_organization_membership(user_id="123", organization_id="456")

    def test_membership_422_without_the_target_pair_is_not_success(self):
        for memberships in (
            [],
            [{"id": 1, "user_id": 123, "organization_id": 789}],
            [{"id": 1, "user_id": 789, "organization_id": 456}],
        ):
            for use_snapshot in (False, True):
                with self.subTest(memberships=memberships, use_snapshot=use_snapshot):
                    self.expect_memberships()
                    snapshot = (
                        {"memberships": self.client.get_organization_memberships(user_id="123")}
                        if use_snapshot
                        else {}
                    )
                    self.expect(
                        "POST", "organization_memberships", {"error": "RecordInvalid"}, status=422
                    )
                    self.expect(
                        "GET",
                        "users/123/organization_memberships",
                        {"organization_memberships": memberships, "next_page": None},
                    )
                    with self.assertRaises(ZendeskProvisioningConflict) as error:
                        self.client.ensure_organization_membership(
                            user_id="123", organization_id="456", **snapshot
                        )
                    self.assertEqual(error.exception.code, "zendesk_conflict")

    def test_missing_membership_resource_is_a_safe_conflict(self):
        for api_error in ("NotFound", "RecordNotFound"):
            for method, path in (
                ("GET", "users/123/organization_memberships"),
                ("POST", "organization_memberships"),
            ):
                with self.subTest(api_error=api_error, method=method):
                    if method == "POST":
                        self.expect_memberships()
                    self.expect(method, path, {"error": api_error}, status=404)
                    with self.assertRaises(ZendeskProvisioningConflict) as error:
                        self.client.ensure_organization_membership(
                            user_id="123", organization_id="456"
                        )
                    self.assertEqual(error.exception.code, "resource_missing")

    def test_invalid_saved_ids_fail_before_any_provider_request(self):
        for invalid_id in ("", "0", "-1", "１２３", "123/456", "1" * 256):
            with self.subTest(invalid_id=invalid_id):
                if invalid_id:
                    with self.assertRaises(ZendeskProvisioningConflict):
                        self.client.ensure_organization(
                            **self.organization_args, zendesk_id=invalid_id
                        )
                with self.assertRaises(ZendeskProvisioningConflict):
                    self.client.ensure_user(**self.user_args, zendesk_id=invalid_id)
                with self.assertRaises(ZendeskProvisioningConflict):
                    self.client.get_organization_memberships(user_id=invalid_id)
                with self.assertRaises(ZendeskProvisioningConflict):
                    self.client.ensure_organization_membership(
                        user_id="123", organization_id=invalid_id
                    )
                with self.assertRaises(ZendeskProvisioningConflict):
                    self.client.ensure_organization_membership(
                        user_id=invalid_id, organization_id="456"
                    )
                for kwargs in (
                    {"user_id": invalid_id, "organization_ids": ["456"]},
                    {"user_id": "123", "organization_ids": ["456", invalid_id]},
                ):
                    with self.assertRaises(ZendeskProvisioningConflict):
                        self.client.remove_organization_memberships(**kwargs)

    def test_provider_authentication_and_server_errors_remain_classifiable(self):
        for status in (401, 403, 503):
            with self.subTest(status=status):
                self.expect("GET", "users/search", {"error": "ProviderFailure"}, status=status)
                with self.assertRaises(APIException) as error:
                    self.client.ensure_user(**self.user_args)
                self.assertEqual(error.exception.response.status_code, status)
                self.expect_memberships()
                self.expect(
                    "POST",
                    "organization_memberships",
                    {"error": "ProviderFailure"},
                    status=status,
                )
                with self.assertRaises(APIException) as error:
                    self.client.ensure_organization_membership(
                        user_id="123", organization_id="456"
                    )
                self.assertEqual(error.exception.response.status_code, status)
                self.expect_memberships()
                self.expect(
                    "POST", "organization_memberships", {"error": "RecordInvalid"}, status=422
                )
                self.expect(
                    "GET",
                    "users/123/organization_memberships",
                    {"error": "ProviderFailure"},
                    status=status,
                )
                with self.assertRaises(APIException) as error:
                    self.client.ensure_organization_membership(
                        user_id="123", organization_id="456"
                    )
                self.assertEqual(error.exception.response.status_code, status)

    def bind(self):
        self.client.bind_user_identity(
            zendesk_id="123", fxa_uid="authenticated-uid", email=self.user_args["email"]
        )

    def expect_identity_owner(self, *users):
        self.expect("GET", "users/show_many", {"users": list(users), "next_page": None})

    def test_binding_sets_identity_and_preserves_custom_fields(self):
        remote = self.remote_user(user_fields={"user_id": "", "department": "Operations"})
        bound = {
            **remote,
            "external_id": "authenticated-uid",
            "user_fields": {"user_id": "authenticated-uid", "department": "Operations"},
        }
        self.expect("GET", "users/123", {"user": remote})
        self.expect_identity_owner()
        self.expect("PUT", "users/123", {"user": bound})
        self.expect("GET", "users/123", {"user": bound})

        self.bind()

        update = next(request for request in self.requests if request.method == "PUT")
        self.assertEqual(
            json.loads(update.body)["user"],
            {
                "id": 123,
                "external_id": "authenticated-uid",
                "user_fields": {"user_id": "authenticated-uid", "department": "Operations"},
            },
        )
        lookup = next(request for request in self.requests if "show_many" in request.url)
        self.assertEqual(
            parse_qs(urlsplit(lookup.url).query), {"external_ids": ["authenticated-uid"]}
        )

    def test_binding_same_identity_is_a_successful_replay_after_local_rollback(self):
        remote = self.remote_user(
            external_id="authenticated-uid", user_fields={"user_id": "authenticated-uid"}
        )
        for _ in range(2):
            self.expect("GET", "users/123", {"user": remote})
            self.expect_identity_owner(remote)
            self.expect("PUT", "users/123", {"user": remote})
            self.expect("GET", "users/123", {"user": remote})
            self.bind()
        self.assertFalse(any(request.method == "POST" for request in self.requests))

    def test_binding_refuses_a_mismatched_remote_user_before_writing(self):
        for fields in (
            {"id": 999},
            {"email": "other@example.com"},
            {"external_id": "another-identity"},
            {"user_fields": {"user_id": "another-identity"}},
            {"external_id": "authenticated-uid", "user_fields": {"user_id": "another-identity"}},
        ):
            with self.subTest(fields=fields):
                self.expect("GET", "users/123", {"user": self.remote_user(**fields)})
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.bind()
                self.assertEqual(error.exception.code, "account_conflict")
        self.assertTrue(all(request.method == "GET" for request in self.requests))

    def test_binding_rejects_another_external_identity_owner_without_overwriting(self):
        self.expect("GET", "users/123", {"user": self.remote_user()})
        self.expect_identity_owner(self.remote_user(id=987, external_id="authenticated-uid"))
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.bind()
        self.assertEqual(error.exception.code, "account_conflict")
        self.assertTrue(all(request.method == "GET" for request in self.requests))

    def test_binding_requires_fresh_readback_of_both_identity_fields(self):
        bound = self.remote_user(
            external_id="authenticated-uid", user_fields={"user_id": "authenticated-uid"}
        )
        for stale in (
            self.remote_user(),
            self.remote_user(external_id="authenticated-uid"),
            self.remote_user(user_fields={"user_id": "authenticated-uid"}),
        ):
            with self.subTest(stale=stale):
                self.expect("GET", "users/123", {"user": self.remote_user()})
                self.expect_identity_owner()
                self.expect("PUT", "users/123", {"user": bound})
                self.expect("GET", "users/123", {"user": stale})
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.bind()
                self.assertEqual(error.exception.code, "account_conflict")

    def test_binding_missing_saved_remote_user_is_not_recreated(self):
        self.expect("GET", "users/123", {"error": "RecordNotFound"}, status=404)
        with self.assertRaises(ZendeskProvisioningConflict) as error:
            self.bind()
        self.assertEqual(error.exception.code, "resource_missing")
        self.assertTrue(all(request.method == "GET" for request in self.requests))

    def test_binding_conflict_is_safe_and_transient_failure_remains_classifiable(self):
        for status in (422, 503):
            self.expect("GET", "users/123", {"user": self.remote_user()})
            self.expect_identity_owner()
            self.expect("PUT", "users/123", {"error": "Private provider details"}, status=status)
            if status == 422:
                with self.assertRaises(ZendeskProvisioningConflict) as error:
                    self.bind()
                self.assertEqual(error.exception.code, "zendesk_conflict")
                self.assertNotIn("Private provider details", str(error.exception))
            else:
                with self.assertRaises(APIException) as error:
                    self.bind()
                self.assertEqual(error.exception.response.status_code, status)


@override_settings(
    ZENDESK_SUBDOMAIN="provisioning-test",
    ZENDESK_USER_EMAIL="provisioner@example.com",
    ZENDESK_API_TOKEN="test-api-token",
    ZENDESK_OAUTH_CLIENT_ID="",
    ZENDESK_OAUTH_CLIENT_SECRET="",
)
class ZendeskMembershipProvisioningTests(ZendeskProvisioningTransportMixin, TestCase):
    def test_join_and_rerun_preserve_unmapped_agent_organization(self):
        company = EnterpriseCompanyFactory()
        mapping = ZendeskOrganization.objects.create(group_profile=company, zendesk_id="456")
        ZendeskOrganization.objects.create(
            group_profile=EnterpriseCompanyFactory(), zendesk_id="789"
        )
        ZendeskOrganization.objects.create(group_profile=EnterpriseCompanyFactory())
        user = UserFactory(email=self.user_args["email"], profile__zendesk_id="123")

        for target_exists in (False, True):
            with self.subTest(target_exists=target_exists):
                start = len(self.requests)
                self.expect("GET", "organizations/456", {"organization": {"id": 456}})
                self.expect("GET", "users/123", {"user": self.remote_user()})
                self.expect_memberships(
                    890,
                    default_organization_id=890,
                    next_page=(
                        "https://provisioning-test.zendesk.com/api/v2/"
                        "users/123/organization_memberships.json?page=2"
                    ),
                )
                self.expect(
                    "GET",
                    "users/123/organization_memberships",
                    {
                        "organization_memberships": [
                            {
                                "id": 3 if target_exists else 2,
                                "user_id": 123,
                                "organization_id": 456 if target_exists else 789,
                            }
                        ],
                        "next_page": None,
                    },
                )
                if not target_exists:
                    self.expect("DELETE", "organization_memberships/2", None, status=204)
                    self.expect(
                        "POST",
                        "organization_memberships",
                        {
                            "organization_membership": {
                                "id": 3,
                                "user_id": 123,
                                "organization_id": 456,
                            }
                        },
                        status=201,
                    )

                progress = ZendeskProvisioningProgress()
                provision_zendesk_membership(
                    client=self.client,
                    company=company,
                    mapping=mapping,
                    profile=user.profile,
                    email=user.email,
                    name=user.profile.display_name,
                    progress=progress,
                )

                self.assertEqual(progress.organization_id, "456")
                self.assertEqual(progress.user_id, "123")
                self.assertEqual(
                    [request.method for request in self.requests[start:]],
                    ["GET"] * 4 if target_exists else ["GET"] * 4 + ["DELETE", "POST"],
                )
                self.assertEqual(
                    parse_qs(urlsplit(self.requests[start + 3].url).query), {"page": ["2"]}
                )


class ZendeskConfigurationChecksTests(TestCase):
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

    def test_chat_configuration_warns_when_partial_or_missing_while_switched_on(self):
        for widget, secret, key_id, switch, expected in (
            ("", "", "", False, []),
            ("", "", "", True, ["customercare.W003"]),
            ("widget", "", "", True, ["customercare.W002"]),
            ("", "secret", "key-id", False, ["customercare.W002"]),
            ("widget", "secret", "key-id", True, []),
        ):
            with self.subTest(widget=widget, secret=secret, key_id=key_id, switch=switch):
                with (
                    self.settings(
                        ZENDESK_CHAT_WIDGET_KEY=widget,
                        ZENDESK_CHAT_SIGNING_SECRET=secret,
                        ZENDESK_CHAT_SIGNING_KEY_ID=key_id,
                    ),
                    override_switch("zendesk-chat", active=switch),
                ):
                    warnings = check_zendesk_chat_configuration(None) + check_zendesk_chat_switch(
                        None, databases=["default"]
                    )
                self.assertEqual([warning.id for warning in warnings], expected)

        # Quiet unless databases are named, and before the switch table exists.
        with (
            self.settings(
                ZENDESK_CHAT_WIDGET_KEY="",
                ZENDESK_CHAT_SIGNING_SECRET="",
                ZENDESK_CHAT_SIGNING_KEY_ID="",
            ),
            override_switch("zendesk-chat", active=True),
        ):
            self.assertEqual(check_zendesk_chat_switch(None), [])
            with patch("waffle.switch_is_active", side_effect=ProgrammingError):
                self.assertEqual(check_zendesk_chat_switch(None, databases=["default"]), [])
