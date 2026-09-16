from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import AnonymousUser, Group
from django.utils import timezone
from zenpy.lib.exception import APIException, RecordNotFoundException

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.customercare.utils import (
    generate_classification_tags,
    process_zendesk_classification_result,
    resolve_chat_eligibility,
    resolve_org_group,
    resolve_user_org_group,
    send_support_ticket_to_zendesk,
    sync_ticket_from_zendesk,
)
from kitsune.groups.models import GroupProfile
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.products.models import ProductSupportConfig
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    TopicFactory,
    ZendeskConfigFactory,
    ZendeskTopicConfigurationFactory,
    ZendeskTopicFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


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
        topic = TopicFactory(
            title="Settings", parent=None, is_archived=False, legacy_tag="technical"
        )
        topic.products.add(self.product)

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Settings"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-settings", "technical"])

    def test_two_tier_topic(self):
        """Test generating tags for a tier 2 topic."""
        tier1 = TopicFactory(
            title="Settings", parent=None, is_archived=False, legacy_tag="technical"
        )
        tier1.products.add(self.product)
        tier2 = TopicFactory(title="Notifications", parent=tier1, is_archived=False)
        tier2.products.add(self.product)

        submission = Mock(product=self.product)
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

        submission = Mock(product=self.product)
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

        zendesk_config = ZendeskConfigFactory()
        ProductSupportConfigFactory(product=self.product, zendesk_config=zendesk_config)
        zd_topic = ZendeskTopicFactory(
            topic=tier2, automation_tags=["ssa-sign-in-failure-automation"]
        )
        ZendeskTopicConfigurationFactory(zendesk_config=zendesk_config, zendesk_topic=zd_topic)

        submission = Mock(product=self.product)
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

        submission = Mock(product=self.product)
        result = {"topic_result": {"topic": "Billing and subscriptions"}}

        tags = generate_classification_tags(submission, result)

        self.assertEqual(tags, ["t1-billing-and-subscriptions", "payments"])

    def test_product_reassignment_includes_other_tag(self):
        """Test that product reassignment adds 'other' tag."""
        tier1 = TopicFactory(
            title="Settings", parent=None, is_archived=False, legacy_tag="technical"
        )
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


class ResolveOrgGroupTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        zd = ZendeskConfigFactory(name="zd")
        self.config = ProductSupportConfigFactory(product=self.product, zendesk_config=zd)

        root_group = Group.objects.create(name="firefox-enterprise")
        self.root = GroupProfile.add_root(group=root_group, slug="firefox-enterprise")

        self.c1_group = Group.objects.create(name="company1")
        self.c1 = self.root.add_child(group=self.c1_group, slug="company1")
        SupportOrganizationFactory(config=self.config, group=self.c1_group)

        it_group = Group.objects.create(name="company1.IT")
        self.c1_it = self.c1.add_child(group=it_group, slug="company1-it")

        self.it_user = UserFactory()
        self.it_user.groups.add(it_group)
        self.stranger = UserFactory()

    def test_descendant_member_resolves_to_org_root(self):
        self.assertEqual(resolve_org_group(self.it_user, self.product), self.c1)

    def test_nested_support_organizations_resolves_to_deepest(self):
        """When multiple ancestors are support organizations, pick the nearest (deepest)."""
        SupportOrganizationFactory(config=self.config, group=self.c1_it.group)
        self.assertEqual(resolve_org_group(self.it_user, self.product), self.c1_it)
        self.assertEqual(resolve_user_org_group(self.it_user), self.c1_it)

    def test_non_member_resolves_to_none(self):
        self.assertIsNone(resolve_org_group(self.stranger, self.product))

    def test_ancestor_sibling_and_unrelated_members_do_not_resolve_to_company(self):
        sibling = self.root.add_child(group=Group.objects.create(name="company2"), slug="company2")
        unrelated = GroupProfile.add_root(
            group=Group.objects.create(name="unrelated"), slug="unrelated"
        )
        for profile in (self.root, sibling, unrelated):
            with self.subTest(group=profile.slug):
                self.stranger.groups.set([profile.group])
                self.assertIsNone(resolve_org_group(self.stranger, self.product))
                self.assertIsNone(resolve_user_org_group(self.stranger))

    def test_equal_depth_organizations_resolve_by_slug(self):
        company = self.root.add_child(group=Group.objects.create(name="company0"), slug="company0")
        SupportOrganizationFactory(config=self.config, group=company.group)
        self.it_user.groups.add(company.group)

        self.assertEqual(resolve_org_group(self.it_user, self.product), company)
        self.assertEqual(resolve_user_org_group(self.it_user), company)

    def test_unauthenticated_users_do_not_resolve_to_organization(self):
        for user in (None, AnonymousUser()):
            with self.subTest(user=user):
                self.assertIsNone(resolve_org_group(user, self.product))
                self.assertIsNone(resolve_user_org_group(user))

    def test_inactive_config_only_prevents_product_resolution(self):
        self.config.is_active = False
        self.config.save()

        self.assertIsNone(resolve_org_group(self.it_user, self.product))
        self.assertEqual(resolve_user_org_group(self.it_user), self.c1)

    def test_no_zendesk_config_returns_none(self):
        product2 = ProductFactory()
        ProductSupportConfigFactory(
            product=product2, zendesk_config=None, forum_config=AAQConfigFactory()
        )
        self.assertIsNone(resolve_org_group(self.it_user, product2))

    def test_no_support_organizations_returns_none(self):
        product2 = ProductFactory()
        zd2 = ZendeskConfigFactory(name="zd2")
        ProductSupportConfigFactory(product=product2, zendesk_config=zd2)
        self.assertIsNone(resolve_org_group(self.it_user, product2))

    def test_no_config_returns_none(self):
        product2 = ProductFactory()
        self.assertIsNone(resolve_org_group(self.it_user, product2))


class ResolveChatEligibilityTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.config = ProductSupportConfigFactory(
            product=self.product,
            zendesk_config=ZendeskConfigFactory(),
        )
        self.root = GroupProfile.add_root(
            group=Group.objects.create(name="enterprise"), slug="enterprise"
        )
        self.company = self.root.add_child(
            group=Group.objects.create(name="company"), slug="company"
        )
        self.org = SupportOrganizationFactory(
            config=self.config, group=self.company.group, include_live_chat=True
        )
        department = self.company.add_child(
            group=Group.objects.create(name="department"), slug="department"
        )
        self.team = department.add_child(group=Group.objects.create(name="team"), slug="team")
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
        sibling = self.root.add_child(group=Group.objects.create(name="sibling"), slug="sibling")
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


class ResolveUserOrgGroupTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        zd = ZendeskConfigFactory(name="zd")
        config = ProductSupportConfigFactory(product=self.product, zendesk_config=zd)

        root_group = Group.objects.create(name="firefox-enterprise")
        self.root = GroupProfile.add_root(group=root_group, slug="firefox-enterprise")
        c1_group = Group.objects.create(name="company1")
        self.c1 = self.root.add_child(group=c1_group, slug="company1")
        SupportOrganizationFactory(config=config, group=c1_group)

        it_group = Group.objects.create(name="company1.IT")
        self.c1_it = self.c1.add_child(group=it_group, slug="company1-it")

        self.it_user = UserFactory()
        self.it_user.groups.add(it_group)
        self.stranger = UserFactory()

    def test_member_resolves_to_org_root(self):
        self.assertEqual(resolve_user_org_group(self.it_user), self.c1)

    def test_non_member_returns_none(self):
        self.assertIsNone(resolve_user_org_group(self.stranger))
