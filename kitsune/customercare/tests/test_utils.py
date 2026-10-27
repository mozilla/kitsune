from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import requests
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from waffle.testutils import override_switch
from zenpy.lib.exception import APIException, RecordNotFoundException

from kitsune.customercare.models import SupportTicket, ZendeskOrganization, accepted_context_for
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.customercare.utils import (
    adopt_chat_ticket,
    create_support_ticket,
    generate_classification_tags,
    process_zendesk_classification_result,
    resolve_chat_eligibility,
    send_support_ticket_to_zendesk,
    sync_ticket_from_zendesk,
)
from kitsune.customercare.zendesk import ENTERPRISE_SUPPORT_TAG
from kitsune.flagit.models import FlaggedObject
from kitsune.groups.models import GroupProfile
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportCoverageFactory,
    SupportOrganizationFactory,
    TopicFactory,
    ZendeskConfigFactory,
    ZendeskTopicConfigurationFactory,
    ZendeskTopicFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class GenerateClassificationTagsTests(TestCase):
    """Tests for generate_classification_tags function."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="firefox", title="Firefox")
        self.zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(product=self.product, zendesk_config=self.zendesk_config)

    def test_no_topic_result_returns_undefined(self):
        """Test that missing topic_result returns ['undefined', 'general']."""
        submission = SupportTicket(product=self.product)
        result = {}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])

    def test_undefined_topic_returns_empty_list(self):
        """Test that 'Undefined' topic returns ['undefined', 'general']."""
        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Undefined"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])

    def test_topic_not_found_in_db_returns_undefined(self):
        """Test that topic not found in database returns ['undefined', 'general']."""
        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Nonexistent Topic"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])

    def test_single_tier_topic(self):
        """Test generating tags for a tier 1 topic."""
        topic = TopicFactory(
            title="Settings", parent=None, is_archived=False, legacy_tag="technical"
        )
        topic.products.add(self.product)

        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Settings"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-settings", "technical"])

    def test_missing_context_preserves_topic_and_legacy_tags(self):
        ProductSupportConfig.objects.filter(product=self.product).delete()
        topic = TopicFactory(title="Settings", legacy_tag="technical", products=[self.product])
        for origin in SupportTicket.Origin.values:
            with self.subTest(origin=origin):
                submission = SupportTicket(product=self.product, origin=origin)
                self.assertEqual(
                    generate_classification_tags(
                        submission, {"topic_result": {"topic": topic.title}}
                    ),
                    ["t1-settings", "technical"],
                )

    def test_two_tier_topic(self):
        """Test generating tags for a tier 2 topic."""
        tier1 = TopicFactory(
            title="Settings", parent=None, is_archived=False, legacy_tag="technical"
        )
        tier1.products.add(self.product)
        tier2 = TopicFactory(title="Notifications", parent=tier1, is_archived=False)
        tier2.products.add(self.product)

        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Notifications"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-settings", "t2-notifications", "technical"])

    def test_three_tier_topic(self):
        """Test generating tags for a tier 3 topic."""
        tier1 = TopicFactory(
            title="Settings", parent=None, is_archived=False, legacy_tag="technical"
        )
        tier1.products.add(self.product)
        tier2 = TopicFactory(
            title="Addons, extensions, and themes", parent=tier1, is_archived=False
        )
        tier2.products.add(self.product)
        tier3 = TopicFactory(title="Extensions", parent=tier2, is_archived=False)
        tier3.products.add(self.product)

        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Extensions"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(
            tags, ["t1-settings", "t2-addons-extensions-and-themes", "t3-extensions", "technical"]
        )

    def test_automation_tags_included_when_zendesk_topic_matches(self):
        """Automation tags are appended when a ZendeskTopic links to the classified Topic."""
        tier1 = TopicFactory(
            title="Passwords and sign in", parent=None, is_archived=False, legacy_tag="accounts"
        )
        tier1.products.add(self.product)
        tier2 = TopicFactory(title="Sign in", parent=tier1, is_archived=False)
        tier2.products.add(self.product)

        zd_topic = ZendeskTopicFactory(
            topic=tier2, automation_tags=["ssa-sign-in-failure-automation"]
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.zendesk_config, zendesk_topic=zd_topic
        )

        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Sign in"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(
            tags,
            [
                "t1-passwords-and-sign-in",
                "t2-sign-in",
                "ssa-sign-in-failure-automation",
                "accounts",
            ],
        )

    def test_no_automation_tag_when_no_zendesk_topic_match(self):
        """No automation tag is appended when no ZendeskTopic links to the classified Topic."""
        tier1 = TopicFactory(
            title="Billing and subscriptions",
            parent=None,
            is_archived=False,
            legacy_tag="payments",
        )
        tier1.products.add(self.product)

        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Billing and subscriptions"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-billing-and-subscriptions", "payments"])

    def test_product_reassignment_includes_other_tag(self):
        """Test that product reassignment adds 'other' tag."""
        tier1 = TopicFactory(
            title="Settings", parent=None, is_archived=False, legacy_tag="technical"
        )
        tier1.products.add(self.product)

        submission = SupportTicket(product=self.product)
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

        submission = SupportTicket(product=self.product)
        result = {"topic_result": {"topic": "Settings"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["undefined", "general"])


class SendSupportTicketToZendeskTests(TestCase):
    """Tests for send_support_ticket_to_zendesk error handling."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="mozilla-vpn", title="Mozilla VPN")
        self.zendesk_config = ZendeskConfigFactory(name="Test Config", ticket_form_id="12345")
        ProductSupportConfigFactory(
            product=self.product, zendesk_config=self.zendesk_config, forum_config=None
        )
        self.submission = Mock(spec=SupportTicket)
        self.submission.product = self.product
        self.submission.user = None
        self.submission.subject = "Test"
        self.submission.description = "Test description"
        self.submission.category = "test"
        self.submission.email = "test@example.com"
        self.submission.os = "win64"
        self.submission.country = "US"
        self.submission.update_channel = ""
        self.submission.policy_distribution = ""
        self.submission.urgency = ""
        self.submission.zendesk_tags = []
        self.submission.context = accepted_context_for(self.product, self.zendesk_config)
        self.submission.origin = SupportTicket.Origin.PRODUCT

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
        self.assertEqual(self.submission.submission_status, SupportTicket.STATUS_REJECTED)
        self.submission.save.assert_called_with(update_fields=["submission_status"])

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
        self.assertEqual(self.submission.submission_status, SupportTicket.STATUS_REJECTED)
        self.submission.save.assert_called_with(update_fields=["submission_status"])

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
        self.assertEqual(self.submission.submission_status, SupportTicket.STATUS_FLAGGED)
        self.submission.save.assert_called_with(update_fields=["submission_status"])
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
        self.assertEqual(self.submission.submission_status, SupportTicket.STATUS_FLAGGED)
        self.submission.save.assert_called_with(update_fields=["submission_status"])
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
        self.assertEqual(self.submission.submission_status, SupportTicket.STATUS_SENT)

    @override_settings(
        ZENDESK_SUBDOMAIN="oauth-test",
        ZENDESK_OAUTH_CLIENT_ID="sumo",
        ZENDESK_OAUTH_CLIENT_SECRET="test-client-secret",
    )
    @patch("kitsune.customercare.utils.flag_object")
    @patch("kitsune.customercare.utils.Profile")
    @patch(
        "kitsune.customercare.zendesk.get_oauth_token",
        side_effect=requests.Timeout("OAuth token endpoint timed out"),
    )
    def test_oauth_failure_flags_submission(self, mock_token, mock_profile, mock_flag_object):
        result = send_support_ticket_to_zendesk(self.submission)

        self.assertFalse(result)
        self.assertEqual(self.submission.submission_status, SupportTicket.STATUS_FLAGGED)
        self.submission.save.assert_called_with(update_fields=["submission_status"])
        mock_flag_object.assert_called_once()


class TicketContextCreationAndDeliveryTests(TestCase):
    def setUp(self):
        self.product = ProductFactory(slug="mozilla-vpn")
        self.zendesk_config = ZendeskConfigFactory(ticket_form_id="12345", brand_id="42")
        self.support_config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=self.zendesk_config
        )
        self.coverage = SupportCoverageFactory(
            product=self.product,
            zendesk_config=self.zendesk_config,
            zendesk_product_value="enterprise-vpn",
        )
        self.organization = ZendeskOrganization.objects.create(
            group_profile=self.coverage.contract.company, zendesk_id="321"
        )
        self.user = UserFactory(profile__zendesk_id="456")
        self.user.groups.add(self.coverage.contract.company.group)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_new_ticket_requires_accepted_context(self, mock_classify):
        for accepted_context in (None, {}):
            with self.subTest(accepted_context=accepted_context):
                with self.assertRaisesMessage(ValueError, "requires its accepted context"):
                    create_support_ticket(
                        self.user,
                        self.product,
                        accepted_context=accepted_context,
                        subject="Deployment help",
                    )
        self.assertFalse(SupportTicket.objects.exists())
        mock_classify.assert_not_called()

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_enterprise_creation_preserves_company_and_context(self, mock_classify):
        context = accepted_context_for(self.product, self.zendesk_config, self.coverage)
        ticket = create_support_ticket(
            self.user,
            self.product,
            coverage=self.coverage,
            accepted_context=context,
            subject="Deployment help",
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.org_group, self.coverage.contract.company)
        self.assertEqual(ticket.origin, SupportTicket.Origin.ENTERPRISE)
        self.assertEqual(ticket.coverage, self.coverage)
        self.assertEqual(ticket.accepted_context, context)
        self.assertNotIn(ENTERPRISE_SUPPORT_TAG, ticket.zendesk_tags)

    @patch("kitsune.customercare.tasks.zendesk_submission_classifier.delay")
    def test_product_ticket_of_a_company_and_organization_member_has_no_company(
        self, mock_classify
    ):
        company = self.coverage.contract.company
        SupportOrganizationFactory(config=self.support_config, group=company.group)
        ticket = create_support_ticket(
            self.user,
            self.product,
            accepted_context=accepted_context_for(self.product, self.zendesk_config),
            subject="Billing",
        )
        self.assertIsNone(ticket.org_group)

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_send_uses_accepted_context_after_configuration_changes(self, mock_client):
        tickets = [
            SupportTicketFactory(
                user=self.user,
                product=self.product,
                origin=origin,
                coverage=coverage,
                org_group=coverage.contract.company if coverage else None,
                accepted_context=accepted_context_for(self.product, self.zendesk_config, coverage),
            )
            for origin, coverage in (
                (SupportTicket.Origin.PRODUCT, None),
                (SupportTicket.Origin.ENTERPRISE, self.coverage),
            )
        ]
        replacement = ZendeskConfigFactory(ticket_form_id="67890", brand_id="99")
        self.support_config.zendesk_config = replacement
        self.support_config.save()
        self.coverage.zendesk_config = replacement
        self.coverage.zendesk_product_value = "changed-enterprise-vpn"
        self.coverage.save()
        self.zendesk_config.ticket_form_id = "54321"
        self.zendesk_config.brand_id = "84"
        self.zendesk_config.save()
        contract = self.coverage.contract
        contract.ends_on = timezone.localdate() - timedelta(days=1)
        contract.starts_on = contract.ends_on - timedelta(days=365)
        contract.save()

        for ticket in tickets:
            with self.subTest(origin=ticket.origin):
                ticket.refresh_from_db()
                mock_client.return_value.create_ticket.return_value = Mock(
                    ticket=Mock(id=ticket.pk)
                )
                self.assertTrue(send_support_ticket_to_zendesk(ticket))
                fields = mock_client.return_value.create_ticket.call_args.args[1]
                self.assertEqual(fields["ticket_form_id"], 12345)
                self.assertEqual(fields["brand_id"], 42)
                self.assertEqual(fields["product"], ticket.accepted_context["product_value"])
                self.assertEqual(fields["origin"], ticket.origin)
                if ticket.origin == SupportTicket.Origin.ENTERPRISE:
                    self.assertEqual(fields["organization_id"], self.organization.zendesk_id)
                else:
                    self.assertNotIn("organization_id", fields)

    def test_automation_tags_use_snapshot_but_taxonomy_tags_stay_live(self):
        topic = TopicFactory(products=[self.product], title="Deployment", legacy_tag="technical")
        zd_topic = ZendeskTopicFactory(topic=topic, automation_tags=["accepted-automation"])
        mapping = ZendeskTopicConfigurationFactory(
            zendesk_config=self.zendesk_config, zendesk_topic=zd_topic
        )
        tickets = [
            SupportTicket(
                product=self.product,
                origin=origin,
                coverage=coverage,
                accepted_context=accepted_context_for(self.product, self.zendesk_config, coverage),
            )
            for origin, coverage in (
                (SupportTicket.Origin.PRODUCT, None),
                (SupportTicket.Origin.ENTERPRISE, self.coverage),
            )
        ]
        mapping.zendesk_topic = ZendeskTopicFactory(
            topic=topic, automation_tags=["replacement-automation"]
        )
        mapping.save()
        zd_topic.automation_tags = ["changed-automation"]
        zd_topic.save()
        topic.title = "Updated deployment"
        topic.legacy_tag = "accounts"
        topic.save()
        result = {"topic_result": {"topic": topic.title}}

        for ticket in tickets:
            with self.subTest(origin=ticket.origin):
                self.assertEqual(
                    generate_classification_tags(ticket, result),
                    [*topic.tier_tags, "accepted-automation", "accounts"],
                )
        self.assertEqual(
            generate_classification_tags(SupportTicket(product=self.product), result),
            [*topic.tier_tags, "replacement-automation", "accounts"],
        )

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_legacy_product_ticket_uses_live_config(self, mock_client):
        ticket = SupportTicketFactory(product=self.product, accepted_context={})
        self.zendesk_config.ticket_form_id = "67890"
        self.zendesk_config.brand_id = "99"
        self.zendesk_config.save()
        mock_client.return_value.create_ticket.return_value = Mock(ticket=Mock(id=123))

        self.assertTrue(send_support_ticket_to_zendesk(ticket))

        fields = mock_client.return_value.create_ticket.call_args.args[1]
        self.assertEqual(fields["ticket_form_id"], 67890)
        self.assertEqual(fields["brand_id"], 99)
        self.assertEqual(fields["product"], "firefox-private-network-vpn")

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_invalid_zendesk_ids_flag_instead_of_sending(self, mock_client):
        for field, value in (
            ("ticket_form_id", ""),
            ("ticket_form_id", "invalid"),
            ("brand_id", "invalid"),
        ):
            with self.subTest(field=field, value=value):
                config = ZendeskConfigFactory(**{field: value})
                ticket = SupportTicketFactory(
                    product=self.product,
                    accepted_context=accepted_context_for(self.product, config),
                )

                self.assertFalse(send_support_ticket_to_zendesk(ticket))

                ticket.refresh_from_db()
                self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)
                flag = FlaggedObject.objects.get(object_id=ticket.pk)
                self.assertEqual(flag.reason, FlaggedObject.REASON_OTHER)
                self.assertIn("invalid literal for int()", flag.notes)
        mock_client.assert_not_called()

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_missing_context_flags_instead_of_sending(self, mock_client):
        self.support_config.delete()
        for origin in SupportTicket.Origin:
            with self.subTest(origin=origin):
                ticket = SupportTicketFactory(
                    product=self.product, origin=origin, accepted_context={}
                )

                self.assertFalse(send_support_ticket_to_zendesk(ticket))

                ticket.refresh_from_db()
                self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)
                flag = FlaggedObject.objects.get(object_id=ticket.pk)
                self.assertEqual(flag.reason, FlaggedObject.REASON_OTHER)
                self.assertIn("Failed to send to Zendesk:", flag.notes)
                self.assertFalse(ticket.zendesk_ticket_id)
        mock_client.assert_not_called()


class ProcessZendeskClassificationResultTests(TestCase):
    """Tests for process_zendesk_classification_result."""

    def setUp(self):
        self.product = ProductFactory(slug="firefox-enterprise", title="Firefox Enterprise")
        self.zendesk_config = ZendeskConfigFactory(name="Test Config", ticket_form_id="12345")
        ProductSupportConfigFactory(
            product=self.product, zendesk_config=self.zendesk_config, forum_config=None
        )
        self.submission = Mock(spec=SupportTicket)
        self.submission.product = self.product
        self.submission.topic = None
        self.submission.zendesk_tags = []

    @patch("kitsune.customercare.utils.send_support_ticket_to_zendesk")
    @patch("kitsune.customercare.utils.Profile")
    def test_segmentation_tags_preserved_after_classification(self, mock_profile, mock_send):
        """Segmentation tags from dropdowns must survive NOT_SPAM classification (issue 2865)."""
        self.submission.zendesk_tags = [
            "loginless_ticket",
            "seg-rel-esr",
            "seg-policy-windows-gpo",
            ENTERPRISE_SUPPORT_TAG,
            "stage",
            "obsolete-topic-tag",
        ]
        result = {
            "action": ModerationAction.NOT_SPAM,
            "topic_result": {"topic": "Undefined"},
            "spam_result": {},
        }

        process_zendesk_classification_result(self.submission, result)

        self.assertIn("seg-rel-esr", self.submission.zendesk_tags)
        self.assertIn("seg-policy-windows-gpo", self.submission.zendesk_tags)
        self.assertIn("loginless_ticket", self.submission.zendesk_tags)
        self.assertIn(ENTERPRISE_SUPPORT_TAG, self.submission.zendesk_tags)
        self.assertIn("stage", self.submission.zendesk_tags)
        self.assertNotIn("obsolete-topic-tag", self.submission.zendesk_tags)


class SyncTicketFromZendeskTests(TestCase):
    def setUp(self):
        self.ticket = SupportTicketFactory(zendesk_ticket_id="123")

    def _make_mock_comment(self, *, id, body, html_body=None, public=True):
        mock_comment = MagicMock()
        mock_comment.id = id
        mock_comment.body = body
        mock_comment.html_body = html_body if html_body is not None else f"<p>{body}</p>"
        mock_comment.created_at = "2025-01-01T00:00:00Z"
        mock_comment.public = public
        mock_comment.author.name = "Agent"
        mock_comment.author.id = 99
        return mock_comment

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_updates_comments(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        # Zendesk returns the original ticket description as comments[0],
        # followed by any agent replies.
        description_comment = self._make_mock_comment(id=1, body="Original question")
        reply_comment = self._make_mock_comment(id=2, body="Hello")
        mock_client.get_ticket_comments.return_value = [description_comment, reply_comment]
        mock_zd_ticket = MagicMock()
        mock_zd_ticket.status = "open"
        mock_zd_ticket.updated_at = timezone.now()
        mock_zd_ticket.subject = self.ticket.subject
        mock_zd_ticket.description = self.ticket.description
        mock_client.get_ticket.return_value = mock_zd_ticket

        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertEqual(len(self.ticket.comments), 2)
        self.assertEqual(self.ticket.comments[0]["body"], "<p>Original question</p>")
        self.assertEqual(self.ticket.comments[1]["body"], "<p>Hello</p>")
        self.assertEqual(self.ticket.comments[1]["author"]["name"], "Agent")
        self.assertEqual(self.ticket.zd_status, "open")
        self.assertIsNotNone(self.ticket.last_synced_at)
        # public_comments excludes the description-comment and any private notes.
        self.assertEqual(len(self.ticket.public_comments), 1)
        self.assertEqual(self.ticket.public_comments[0]["body"], "<p>Hello</p>")

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_stores_html_body_not_plain_body(self, mock_client_cls):
        """html_body (rich HTML) is stored, not the plain-text body."""
        mock_client = mock_client_cls.return_value
        comment = self._make_mock_comment(id=1, body="plain", html_body="<p><b>rich</b></p>")
        mock_client.get_ticket_comments.return_value = [comment]
        mock_client.get_ticket.return_value = MagicMock(
            status="open",
            updated_at=timezone.now(),
            subject=self.ticket.subject,
            description=self.ticket.description,
        )

        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.comments[0]["body"], "<p><b>rich</b></p>")
        self.assertNotEqual(self.ticket.comments[0]["body"], "plain")

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_filters_private_comments(self, mock_client_cls):
        """Private comments are stored but excluded from public_comments."""
        mock_client = mock_client_cls.return_value
        description_comment = self._make_mock_comment(id=1, body="Original question")
        private_reply = self._make_mock_comment(id=2, body="Internal note", public=False)
        mock_client.get_ticket_comments.return_value = [description_comment, private_reply]
        mock_client.get_ticket.return_value = MagicMock(
            status="open",
            updated_at=timezone.now(),
            subject=self.ticket.subject,
            description=self.ticket.description,
        )

        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertEqual(len(self.ticket.comments), 2)
        self.assertFalse(self.ticket.comments[1]["public"])
        self.assertEqual(self.ticket.public_comments, [])

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_chat_transcript_comments_have_no_author(self, mock_client_cls):
        """Zendesk records a live chat's messages in transcript comments, which have no author."""
        mock_client = mock_client_cls.return_value
        description_comment = self._make_mock_comment(id=1, body="Conversation with Ringo")
        description_comment.via.channel = "native_messaging"
        transcript = self._make_mock_comment(id=2, body="(13:44:37) Ringo: Hello?")
        transcript.author = None
        transcript.via.channel = "chat_transcript"
        mock_client.get_ticket_comments.return_value = [description_comment, transcript]
        mock_client.get_ticket.return_value = MagicMock(
            status="open",
            updated_at=timezone.now(),
            subject=self.ticket.subject,
            description=self.ticket.description,
        )

        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertEqual(
            [(False, {"name": "Agent", "id": 99}), (True, None)],
            [(c["is_transcript"], c["author"]) for c in self.ticket.comments],
        )

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_updates_subject(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_ticket_comments.return_value = []
        mock_client.get_ticket.return_value = MagicMock(
            status="open",
            updated_at=timezone.now(),
            subject="A renamed ticket",
            description=self.ticket.description,
        )

        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, "A renamed ticket")

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_truncates_long_subject(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_ticket_comments.return_value = []
        mock_client.get_ticket.return_value = MagicMock(
            status="open",
            updated_at=timezone.now(),
            subject="Conversation with " + "x" * 255,
            description=self.ticket.description,
        )

        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, ("Conversation with " + "x" * 255)[:255])

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_updates_description(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_ticket_comments.return_value = []
        mock_client.get_ticket.return_value = MagicMock(
            status="open",
            updated_at=timezone.now(),
            subject=self.ticket.subject,
            description="An updated description from Zendesk",
        )

        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.description, "An updated description from Zendesk")

    @patch("kitsune.customercare.utils.fetch_zendesk_ticket_data")
    def test_skips_deleted_ticket(self, mock_fetch):
        self.ticket.zd_deleted_at = timezone.now()
        self.ticket.save(update_fields=["zd_deleted_at"])

        sync_ticket_from_zendesk(self.ticket)

        mock_fetch.assert_not_called()

    @patch(
        "kitsune.customercare.utils.fetch_zendesk_ticket_data",
        side_effect=RecordNotFoundException,
    )
    def test_record_not_found_marks_ticket_deleted(self, mock_fetch):
        """A ticket deleted in Zendesk before we fetch it self-heals to read-only."""
        sync_ticket_from_zendesk(self.ticket)

        self.ticket.refresh_from_db()
        self.assertIsNotNone(self.ticket.zd_deleted_at)


@override_switch("zendesk-chat", active=True)
@override_settings(
    ZENDESK_CHAT_WIDGET_KEY="test-widget-key",
    ZENDESK_CHAT_SIGNING_SECRET="test-signing-secret",
    ZENDESK_CHAT_SIGNING_KEY_ID="test-key-id",
)
class ResolveChatEligibilityTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.config = ProductSupportConfigFactory(
            product=self.product,
            zendesk_config=ZendeskConfigFactory(),
        )
        self.root = GroupProfile.objects.add_root(
            create_kwargs={"group": Group.objects.create(name="enterprise"), "slug": "enterprise"}
        )
        self.company = GroupProfile.objects.add_child(
            self.root,
            create_kwargs={"group": Group.objects.create(name="company"), "slug": "company"},
        )
        self.org = SupportOrganizationFactory(
            config=self.config, group=self.company.group, include_live_chat=True
        )
        department = GroupProfile.objects.add_child(
            self.company,
            create_kwargs={"group": Group.objects.create(name="department"), "slug": "department"},
        )
        self.team = GroupProfile.objects.add_child(
            department, create_kwargs={"group": Group.objects.create(name="team"), "slug": "team"}
        )
        self.user = UserFactory()
        self.user.groups.add(self.company.group)

    def _assert_eligible(self, result):
        self.assertTrue(result.eligible)
        self.assertEqual(result.org, self.org)
        self.assertIsNone(result.reason)

    def _assert_ineligible(self, result, reason):
        self.assertFalse(result.eligible)
        self.assertIsNone(result.org)
        self.assertEqual(result.reason, reason)

    @override_switch("zendesk-chat", active=False)
    def test_switch_off(self):
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "chat_is_disabled"
        )

    def test_switched_on_but_not_configured(self):
        for setting in (
            "ZENDESK_CHAT_WIDGET_KEY",
            "ZENDESK_CHAT_SIGNING_SECRET",
            "ZENDESK_CHAT_SIGNING_KEY_ID",
        ):
            with self.subTest(setting=setting), self.settings(**{setting: ""}):
                self._assert_ineligible(
                    resolve_chat_eligibility(self.user, self.product), "chat_not_configured"
                )

    def test_membership_resolves_one_org_per_product(self):
        self.config.forum_config = AAQConfigFactory()
        self.config.default_support_type = ProductSupportConfig.SUPPORT_TYPE_FORUM
        self.config.group_default_support_type = ProductSupportConfig.SUPPORT_TYPE_FORUM
        self.config.save()
        SupportOrganizationFactory(
            config=ProductSupportConfigFactory(zendesk_config=ZendeskConfigFactory()),
            group=self.company.group,
            include_live_chat=True,
        )
        for profile in (self.company, self.team):
            with self.subTest(group=profile.slug):
                self.user.groups.set([profile.group])
                self._assert_eligible(resolve_chat_eligibility(self.user, self.product))
        self.user.groups.add(self.company.group)
        self._assert_eligible(resolve_chat_eligibility(self.user, self.product))

    def test_ancestor_and_sibling_members_do_not_receive_chat(self):
        sibling = GroupProfile.objects.add_child(
            self.root,
            create_kwargs={"group": Group.objects.create(name="sibling"), "slug": "sibling"},
        )
        for profile in (self.root, sibling):
            with self.subTest(group=profile.slug):
                self.user.groups.set([profile.group])
                self._assert_ineligible(
                    resolve_chat_eligibility(self.user, self.product), "no_entitled_org"
                )

    def test_leadership_does_not_grant_chat(self):
        self.user.groups.clear()
        self.company.leaders.add(self.user)
        self.root.leaders.add(self.user)
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "no_entitled_org"
        )

    def test_moderated_visibility_does_not_grant_chat(self):
        self.root.update_visibility(GroupProfile.Visibility.MODERATED)
        auditors = Group.objects.create(name="auditors")
        self.root.visible_to_groups.add(auditors)
        self.company.visible_to_groups.add(auditors)
        self.user.groups.set([auditors])
        self.assertTrue(self.company.can_view(self.user))
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "no_entitled_org"
        )

    def test_staff_and_superuser_privileges_do_not_grant_chat(self):
        self.user.groups.clear()
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "no_entitled_org"
        )

    def test_authentication_and_archived_product_guards(self):
        for user in (None, AnonymousUser()):
            with self.subTest(user=user):
                self._assert_ineligible(
                    resolve_chat_eligibility(user, self.product), "not_authenticated"
                )
        self.user.is_active = False
        self.user.save()
        self._assert_ineligible(resolve_chat_eligibility(self.user, self.product), "inactive_user")
        self.user.is_active = True
        self.user.save()
        self.product.is_archived = True
        self.product.save()
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "product_unavailable"
        )

    def test_missing_or_forum_only_config_has_no_ticketing_support(self):
        product = ProductFactory()
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, product), "no_ticketing_support"
        )
        ProductSupportConfigFactory(
            product=product, zendesk_config=None, forum_config=AAQConfigFactory()
        )
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, product), "no_ticketing_support"
        )

    def test_membership_for_another_product_does_not_grant_chat(self):
        requested = ProductFactory()
        ProductSupportConfigFactory(product=requested, zendesk_config=ZendeskConfigFactory())
        self._assert_ineligible(resolve_chat_eligibility(self.user, requested), "no_entitled_org")

    def test_nested_legacy_orgs_are_ambiguous_only_with_chat(self):
        nested_org = SupportOrganizationFactory(
            config=self.config, group=self.team.group, include_live_chat=False
        )
        self.user.groups.set([self.team.group])
        self._assert_eligible(resolve_chat_eligibility(self.user, self.product))

        nested_org.include_live_chat = True
        nested_org.save()
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "ambiguous_multi_org"
        )

    def test_subscription_is_required_but_does_not_replace_org_membership(self):
        self.config.subscription_only = True
        self.config.save()
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "subscription_required"
        )
        self.user.profile.products.add(self.product)
        self._assert_eligible(resolve_chat_eligibility(self.user, self.product))
        self.user.groups.clear()
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "no_entitled_org"
        )

    def test_config_changes_are_not_cached(self):
        self._assert_eligible(resolve_chat_eligibility(self.user, self.product))
        self.config.is_active = False
        self.config.save()
        self._assert_ineligible(
            resolve_chat_eligibility(self.user, self.product), "no_ticketing_support"
        )
        self.config.is_active = True
        self.config.save()
        self._assert_eligible(resolve_chat_eligibility(self.user, self.product))


def set_up_live_chat(product):
    """Offer live chat on the product through an org, and return the org's group."""
    config = ProductSupportConfigFactory(product=product, zendesk_config=ZendeskConfigFactory())
    root = GroupProfile.add_root(group=Group.objects.create(name="chat"), slug="chat")
    company = root.add_child(group=Group.objects.create(name="company"), slug="company")
    SupportOrganizationFactory(config=config, group=company.group, include_live_chat=True)
    return company


def chatter(org, fxa_uid="fxa-123"):
    """A member of the org whose Zendesk user carries the given fxa_uid."""
    user = UserFactory()
    user.groups.add(org.group)
    # Saved without signals, so nothing reaches out to Zendesk.
    Profile.objects.filter(user=user).update(fxa_uid=fxa_uid)
    return user


@override_switch("zendesk-chat", active=True)
@override_settings(
    ZENDESK_CHAT_WIDGET_KEY="test-widget-key",
    ZENDESK_CHAT_SIGNING_SECRET="test-signing-secret",
    ZENDESK_CHAT_SIGNING_KEY_ID="test-key-id",
)
@patch("kitsune.customercare.utils.ZendeskClient")
class AdoptChatTicketTests(TestCase):
    def setUp(self):
        self.product = ProductFactory(slug="firefox-enterprise")
        self.org = set_up_live_chat(self.product)
        self.user = chatter(self.org)

    def _zd_ticket(self, **overrides):
        attrs = {
            "id": 555,
            "via": Mock(channel=SupportTicket.ZD_CHANNEL_MESSAGING),
            "requester_id": 789,
            "tags": ["product-firefox-enterprise"],
            "created_at": "2026-09-20T10:00:00Z",
            "updated_at": "2026-09-20T10:05:00Z",
            "status": "open",
            "subject": "Conversation with Ringo",
            "description": "My printer is on fire",
        }
        attrs.update(overrides)
        return Mock(**attrs)

    def _comment(self, id, body):
        comment = MagicMock(id=id, html_body=f"<p>{body}</p>", public=True)
        comment.created_at = "2026-09-20T10:00:00Z"
        comment.author.name = "Ringo"
        comment.author.id = 789
        return comment

    def _mock_zendesk(self, mock_client, external_id="fxa-123"):
        client = mock_client.return_value
        client.get_user.return_value = Mock(external_id=external_id)
        client.get_ticket_comments.return_value = [
            self._comment(1, "My printer is on fire"),
            self._comment(2, "Have you tried water?"),
        ]
        return client

    def test_creates_the_ticket(self, mock_client):
        self._mock_zendesk(mock_client)

        ticket = adopt_chat_ticket(self._zd_ticket())

        ticket.refresh_from_db()
        self.assertEqual("555", ticket.zendesk_ticket_id)
        self.assertEqual(self.user, ticket.user)
        self.assertEqual(self.user.email, ticket.email)
        self.assertEqual(self.product, ticket.product)
        self.assertEqual(self.org, ticket.org_group)
        self.assertTrue(ticket.is_chat)
        self.assertEqual(SupportTicket.STATUS_SENT, ticket.submission_status)
        self.assertEqual(parse_datetime("2026-09-20T10:00:00Z"), ticket.created)
        self.assertEqual("Conversation with Ringo", ticket.subject)
        self.assertEqual(SupportTicket.ZD_STATUS_OPEN, ticket.zd_status)
        self.assertEqual(2, len(ticket.comments))
        self.assertIsNotNone(ticket.last_synced_at)

    @override_settings(ZENDESK_CHAT_WIDGET_KEY="")
    def test_missing_chat_settings_prevent_adoption(self, mock_client):
        self._mock_zendesk(mock_client)

        with self.assertRaises(ImproperlyConfigured):
            adopt_chat_ticket(self._zd_ticket())
        self.assertFalse(SupportTicket.objects.exists())

    def test_a_chat_from_someone_who_can_no_longer_chat_gets_no_organization(self, mock_client):
        """The chat is still recorded, but no organization sees it."""
        self._mock_zendesk(mock_client)
        self.user.groups.remove(self.org.group)

        ticket = adopt_chat_ticket(self._zd_ticket())

        self.assertEqual(self.user, ticket.user)
        self.assertIsNone(ticket.org_group)

    def test_adopting_the_same_chat_again_returns_the_same_ticket(self, mock_client):
        self._mock_zendesk(mock_client)

        first = adopt_chat_ticket(self._zd_ticket())
        second = adopt_chat_ticket(self._zd_ticket())

        self.assertEqual(first.id, second.id)
        self.assertEqual(1, SupportTicket.objects.count())

    def test_a_ticket_that_is_not_a_chat_is_left_alone(self, mock_client):
        self._mock_zendesk(mock_client)

        self.assertIsNone(adopt_chat_ticket(self._zd_ticket(via=Mock(channel="email"))))
        self.assertFalse(SupportTicket.objects.exists())
        mock_client.return_value.get_user.assert_not_called()

    def test_a_chat_from_someone_we_cannot_find_is_left_alone(self, mock_client):
        self._mock_zendesk(mock_client, external_id="fxa-unknown")

        with self.assertLogs("k.customercare", level="ERROR"):
            self.assertIsNone(adopt_chat_ticket(self._zd_ticket()))
        self.assertFalse(SupportTicket.objects.exists())

    def test_ignores_zendesk_ids_saved_on_profiles(self, mock_client):
        """A saved Zendesk id can be shared or stale, so it never decides the match."""
        someone_else = UserFactory()
        Profile.objects.filter(user=someone_else).update(zendesk_id="789", fxa_uid="fxa-456")
        self._mock_zendesk(mock_client)

        ticket = adopt_chat_ticket(self._zd_ticket())

        self.assertEqual(self.user, ticket.user)

    def test_a_chat_from_a_zendesk_user_without_an_external_id_is_left_alone(self, mock_client):
        """For example, someone who only ever filed a ticket without signing in."""
        # Without the external_id check, this user would match fxa_uid=None.
        no_fxa = UserFactory()
        Profile.objects.filter(user=no_fxa).update(fxa_uid=None)
        self._mock_zendesk(mock_client, external_id=None)

        with self.assertLogs("k.customercare", level="ERROR"):
            self.assertIsNone(adopt_chat_ticket(self._zd_ticket()))
        self.assertFalse(SupportTicket.objects.exists())

    def test_a_chat_whose_zendesk_user_is_gone_is_left_alone(self, mock_client):
        self._mock_zendesk(mock_client)
        mock_client.return_value.get_user.side_effect = RecordNotFoundException

        with self.assertLogs("k.customercare", level="ERROR"):
            self.assertIsNone(adopt_chat_ticket(self._zd_ticket()))
        self.assertFalse(SupportTicket.objects.exists())

    def test_a_chat_without_a_product_tag_is_left_alone(self, mock_client):
        self._mock_zendesk(mock_client)

        with self.assertNoLogs("k.customercare"):
            self.assertIsNone(adopt_chat_ticket(self._zd_ticket(tags=["stage"])))
        self.assertFalse(SupportTicket.objects.exists())
        # Checked before the user lookup, so these chats cost the sweep nothing.
        mock_client.return_value.get_user.assert_not_called()

    def test_a_chat_tagged_with_an_unknown_product_is_left_alone(self, mock_client):
        self._mock_zendesk(mock_client)

        with self.assertLogs("k.customercare", level="ERROR"):
            self.assertIsNone(adopt_chat_ticket(self._zd_ticket(tags=["product-gone"])))
        self.assertFalse(SupportTicket.objects.exists())
        mock_client.return_value.get_user.assert_not_called()
