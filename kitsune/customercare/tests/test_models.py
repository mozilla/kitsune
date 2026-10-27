from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.utils import timezone

from kitsune.customercare.models import (
    MissingTicketContext,
    SupportTicket,
    ZendeskOrganization,
    accepted_context_for,
)
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.groups.models import GroupProfile
from kitsune.groups.tests import DepartmentFactory, EnterpriseCompanyFactory, GroupProfileFactory
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportContractFactory,
    SupportCoverageFactory,
    TopicFactory,
    ZendeskConfigFactory,
    ZendeskTopicConfigurationFactory,
)
from kitsune.questions.tests import AAQConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class SupportTicketModelTests(TestCase):
    """Tests for SupportTicket model."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory()

    def test_status_choices_include_processing_failed(self):
        """Test that STATUS_PROCESSING_FAILED is a valid status choice."""
        status_values = [choice[0] for choice in SupportTicket.SUBMISSION_STATUS_CHOICES]
        self.assertIn(SupportTicket.STATUS_PROCESSING_FAILED, status_values)
        self.assertEqual(SupportTicket.STATUS_PROCESSING_FAILED, "processing_failed")

    def test_create_ticket_with_processing_failed_status(self):
        """Test that tickets can be created with STATUS_PROCESSING_FAILED."""
        ticket = SupportTicket.objects.create(
            subject="Test",
            description="Test description",
            category="test",
            email="test@example.com",
            product=self.product,
            submission_status=SupportTicket.STATUS_PROCESSING_FAILED,
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_PROCESSING_FAILED)

    def test_default_status_is_pending(self):
        """Test that default status is STATUS_PENDING."""
        ticket = SupportTicket.objects.create(
            subject="Test",
            description="Test description",
            category="test",
            email="test@example.com",
            product=self.product,
        )

        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_PENDING)

    def test_str_method(self):
        """Test the __str__ method includes status."""
        ticket = SupportTicket.objects.create(
            subject="Test Subject",
            description="Test description",
            category="test",
            email="test@example.com",
            product=self.product,
            submission_status=SupportTicket.STATUS_PROCESSING_FAILED,
        )

        str_repr = str(ticket)
        self.assertIn("Test Subject", str_repr)
        self.assertIn("processing_failed", str_repr)


class AcceptedTicketContextTests(TestCase):
    def setUp(self):
        self.product = ProductFactory(slug="mozilla-vpn")
        self.config = ZendeskConfigFactory(ticket_form_id="42", brand_id="17")
        ProductSupportConfigFactory(product=self.product, zendesk_config=self.config)
        self.topic = TopicFactory(products=[self.product])
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.config,
            zendesk_topic__topic=self.topic,
            zendesk_topic__slug="a-first",
            zendesk_topic__automation_tags=["vpn-automation"],
        )
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.config, zendesk_topic__automation_tags=["unlinked"]
        )
        ZendeskTopicConfigurationFactory(
            zendesk_topic__topic=self.topic, zendesk_topic__automation_tags=["other-config"]
        )

    def test_product_context_snapshots_config_and_vpn_alias(self):
        self.assertEqual(
            accepted_context_for(self.product, self.config),
            {
                "form_id": "42",
                "brand_id": "17",
                "product_value": "firefox-private-network-vpn",
                "skip_spam": False,
                "automation_tags": {str(self.topic.pk): ["vpn-automation"]},
            },
        )
        self.product.slug = "mozilla-account"
        self.config.brand_id = ""
        self.config.skip_spam_moderation = True
        context = accepted_context_for(self.product, self.config)
        self.assertEqual(context["product_value"], "mozilla-account")
        self.assertEqual(context["brand_id"], "")
        self.assertTrue(context["skip_spam"])

    def test_enterprise_context_snapshots_coverage_and_company(self):
        coverage = SupportCoverageFactory(
            product=self.product,
            zendesk_config=self.config,
            zendesk_product_value="enterprise-vpn",
        )
        company = coverage.contract.company
        context = accepted_context_for(self.product, self.config, coverage)
        self.assertEqual(context["product_value"], "enterprise-vpn")
        self.assertTrue(context["skip_spam"])
        self.assertEqual(context["coverage_id"], coverage.pk)
        self.assertEqual(
            context["contract"], {"id": coverage.contract_id, "name": coverage.contract.name}
        )
        self.assertEqual(
            context["company"],
            {
                "external_id": str(
                    ZendeskOrganization.objects.get(group_profile=company).external_id
                ),
                "name": company.group.name,
            },
        )
        self.assertEqual(context, accepted_context_for(self.product, self.config, coverage))

    def test_first_zendesk_topic_by_slug_supplies_automation_tags(self):
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.config,
            zendesk_topic__topic=self.topic,
            zendesk_topic__slug="z-last",
            zendesk_topic__automation_tags=["other-automation"],
        )
        context = accepted_context_for(self.product, self.config)
        self.assertEqual(context["automation_tags"], {str(self.topic.pk): ["vpn-automation"]})

    def test_missing_live_zendesk_config_raises_missing_context(self):
        config = ProductSupportConfigFactory(
            product=ProductFactory(), forum_config=AAQConfigFactory(), zendesk_config=None
        )
        ticket = SupportTicketFactory(product=config.product)
        with self.assertRaisesMessage(MissingTicketContext, "active Zendesk config"):
            ticket.context
        config.delete()
        with self.assertRaisesMessage(MissingTicketContext, "active Zendesk config"):
            ticket.context


class PublicCommentsTests(TestCase):
    """Tests for SupportTicket.public_comments and num_answers.

    After the first sync, Zendesk returns the original ticket description as
    the first item in the comments list. public_comments must skip that first
    comment so the description (already rendered as the question body) does
    not appear as a duplicate reply. Before the first sync, the comments list
    can only contain webhook-appended replies, so nothing should be skipped.
    See issue #3035.
    """

    def setUp(self):
        self.product = ProductFactory()

    def _make_ticket(self, comments, *, synced=True):
        return SupportTicket.objects.create(
            subject="Test",
            description="The original question",
            category="test",
            email="test@example.com",
            product=self.product,
            comments=comments,
            last_synced_at=timezone.now() if synced else None,
        )

    def test_empty_comments(self):
        ticket = self._make_ticket([])
        self.assertEqual(ticket.public_comments, [])
        self.assertEqual(ticket.num_answers, 0)

    def test_only_description_comment(self):
        ticket = self._make_ticket(
            [
                {"id": 1, "body": "The original question", "public": True},
            ]
        )
        self.assertEqual(ticket.public_comments, [])
        self.assertEqual(ticket.num_answers, 0)

    def test_description_plus_public_replies(self):
        ticket = self._make_ticket(
            [
                {"id": 1, "body": "The original question", "public": True},
                {"id": 2, "body": "First reply", "public": True},
                {"id": 3, "body": "Second reply", "public": True},
            ]
        )
        bodies = [c["body"] for c in ticket.public_comments]
        self.assertEqual(bodies, ["First reply", "Second reply"])
        self.assertEqual(ticket.num_answers, 2)

    def test_description_plus_mixed_public_and_private(self):
        ticket = self._make_ticket(
            [
                {"id": 1, "body": "The original question", "public": True},
                {"id": 2, "body": "Public reply", "public": True},
                {"id": 3, "body": "Internal note", "public": False},
                {"id": 4, "body": "Another public reply", "public": True},
            ]
        )
        bodies = [c["body"] for c in ticket.public_comments]
        self.assertEqual(bodies, ["Public reply", "Another public reply"])
        self.assertEqual(ticket.num_answers, 2)

    def test_pre_sync_webhook_reply_is_not_skipped(self):
        """If a webhook adds a comment before the first sync, comments[0] is
        the webhook reply (not the description) and must not be sliced off.
        """
        ticket = self._make_ticket(
            [
                {"id": 99, "body": "Webhook reply", "public": True},
            ],
            synced=False,
        )
        bodies = [c["body"] for c in ticket.public_comments]
        self.assertEqual(bodies, ["Webhook reply"])
        self.assertEqual(ticket.num_answers, 1)

    def test_pre_sync_filters_private(self):
        ticket = self._make_ticket(
            [
                {"id": 99, "body": "Webhook reply", "public": True},
                {"id": 100, "body": "Internal note", "public": False},
            ],
            synced=False,
        )
        bodies = [c["body"] for c in ticket.public_comments]
        self.assertEqual(bodies, ["Webhook reply"])


class AccessibleToTests(TestCase):
    def setUp(self):
        self.company = EnterpriseCompanyFactory()
        self.department = DepartmentFactory(company=self.company)
        self.other_company = EnterpriseCompanyFactory()
        self.root = GroupProfile.objects.get_parent(self.company)
        self.foreign_group = DepartmentFactory(company=GroupProfileFactory())
        # History never consults coverage: one company's contract expired, the other has none.
        today = timezone.localdate()
        SupportContractFactory(
            company=self.company,
            starts_on=today - timedelta(days=60),
            ends_on=today - timedelta(days=1),
        )

        self.owner = self.member(self.company)
        self.dept_member = self.member(self.department)
        self.other_member = self.member(self.other_company)
        self.company_ticket = SupportTicketFactory(user=self.owner, org_group=self.company)
        self.department_ticket = SupportTicketFactory(
            user=self.dept_member, org_group=self.department
        )
        self.other_ticket = SupportTicketFactory(
            user=self.other_member, org_group=self.other_company
        )
        self.legacy_owner = UserFactory()
        self.personal_ticket = SupportTicketFactory(user=self.legacy_owner)
        self.root_ticket = SupportTicketFactory(user=self.legacy_owner, org_group=self.root)
        self.foreign_ticket = SupportTicketFactory(
            user=self.legacy_owner, org_group=self.foreign_group
        )

    def member(self, *profiles):
        user = UserFactory()
        user.groups.add(*(profile.group for profile in profiles))
        return user

    def leader(self, profile):
        user = UserFactory()
        profile.leaders.add(user)
        return user

    def test_audience_is_keyed_on_the_owning_enterprise_group(self):
        all_tickets = {
            self.company_ticket,
            self.department_ticket,
            self.other_ticket,
            self.personal_ticket,
            self.root_ticket,
            self.foreign_ticket,
        }
        for persona, user, expected in (
            ("anonymous", AnonymousUser(), set()),
            ("none", None, set()),
            ("staff", UserFactory(is_staff=True), all_tickets),
            ("owner", self.owner, {self.company_ticket}),
            ("company teammate", self.member(self.company), {self.company_ticket}),
            ("department member", self.dept_member, {self.company_ticket, self.department_ticket}),
            (
                "department teammate",
                self.member(self.department),
                {self.company_ticket, self.department_ticket},
            ),
            ("company leader", self.leader(self.company), {self.company_ticket}),
            ("department leader", self.leader(self.department), {self.department_ticket}),
            (
                "root leader",
                self.leader(self.root),
                {self.company_ticket, self.department_ticket, self.other_ticket},
            ),
            ("root-only member", self.member(self.root), set()),
            ("foreign root leader", self.leader(self.foreign_group.get_parent()), set()),
            ("other company member", self.other_member, {self.other_ticket}),
            ("foreign group member", self.member(self.foreign_group), set()),
            (
                "owner of personal and legacy tickets",
                self.legacy_owner,
                {self.personal_ticket, self.root_ticket, self.foreign_ticket},
            ),
        ):
            with self.subTest(persona=persona):
                self.assertEqual(set(SupportTicket.objects.accessible_to(user)), expected)

    def test_only_the_owner_can_reply(self):
        for user, can_reply in (
            (self.owner, True),
            (self.member(self.company), False),
            (self.leader(self.root), False),
            (AnonymousUser(), False),
            (None, False),
        ):
            with self.subTest(user=user):
                self.assertEqual(self.company_ticket.can_reply(user), can_reply)

    def test_not_even_the_owner_can_reply_to_a_chat(self):
        """Replies never reach the widget, so a chat takes none at all."""
        self.company_ticket.zd_channel = SupportTicket.ZD_CHANNEL_MESSAGING
        self.assertFalse(self.company_ticket.can_reply(self.owner))


class IsSyncableTests(TestCase):
    """is_syncable is True only with a usable Zendesk id and no deletion."""

    def test_syncable_with_id_and_not_deleted(self):
        ticket = SupportTicketFactory(zendesk_ticket_id="123")
        self.assertTrue(ticket.is_syncable)

    def test_not_syncable_when_deleted(self):
        ticket = SupportTicketFactory(zendesk_ticket_id="123", zd_deleted_at=timezone.now())
        self.assertFalse(ticket.is_syncable)

    def test_not_syncable_with_null_id(self):
        ticket = SupportTicketFactory(zendesk_ticket_id=None)
        self.assertFalse(ticket.is_syncable)

    def test_not_syncable_with_blank_id(self):
        ticket = SupportTicketFactory(zendesk_ticket_id="")
        self.assertFalse(ticket.is_syncable)


class ZendeskTicketIdTests(TestCase):
    """Only one SupportTicket may point at a given Zendesk ticket."""

    def test_two_tickets_cannot_share_a_zendesk_ticket(self):
        SupportTicketFactory(zendesk_ticket_id="555")

        with self.assertRaises(IntegrityError), transaction.atomic():
            SupportTicketFactory(zendesk_ticket_id="555")

    def test_tickets_not_yet_sent_to_zendesk_can_share_an_empty_id(self):
        for zendesk_ticket_id in (None, None, "", ""):
            SupportTicketFactory(zendesk_ticket_id=zendesk_ticket_id)

        self.assertEqual(4, SupportTicket.objects.count())


class StatusLabelTests(TestCase):
    """status_label derives the user-facing status string."""

    def test_deleted_is_inactive_regardless_of_status(self):
        ticket = SupportTicketFactory(
            zendesk_ticket_id="123",
            zd_status=SupportTicket.ZD_STATUS_SOLVED,
            zd_deleted_at=timezone.now(),
        )
        self.assertEqual(str(ticket.status_label), "Inactive")

    def test_zd_status_maps_to_display(self):
        ticket = SupportTicketFactory(
            zendesk_ticket_id="123", zd_status=SupportTicket.ZD_STATUS_SOLVED
        )
        self.assertEqual(str(ticket.status_label), "Solved")

    def test_no_zd_status_is_submitted(self):
        ticket = SupportTicketFactory(zendesk_ticket_id="123", zd_status=None)
        self.assertEqual(str(ticket.status_label), "Submitted")


class SupportTicketQuerySetTests(TestCase):
    """Tests for SupportTicketQuerySet.syncable / active / solved.

    active() and solved() are display filters (status + not deleted), so they
    include tickets that have not yet synced a Zendesk id. syncable() is the
    sync-eligibility filter and mirrors is_syncable: a usable id and no deletion.
    The sync dispatch chains active().syncable().
    """

    def setUp(self):
        self.product = ProductFactory()
        self.live_open = self._make(zendesk_ticket_id="1", zd_status=SupportTicket.ZD_STATUS_OPEN)
        self.live_solved = self._make(
            zendesk_ticket_id="2", zd_status=SupportTicket.ZD_STATUS_SOLVED
        )
        self.closed = self._make(zendesk_ticket_id="3", zd_status=SupportTicket.ZD_STATUS_CLOSED)
        self.no_status = self._make(zendesk_ticket_id="4", zd_status=None)
        self.deleted_open = self._make(
            zendesk_ticket_id="5",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
            zd_deleted_at=timezone.now(),
        )
        self.null_id_open = self._make(
            zendesk_ticket_id=None, zd_status=SupportTicket.ZD_STATUS_OPEN
        )
        self.blank_id_open = self._make(
            zendesk_ticket_id="", zd_status=SupportTicket.ZD_STATUS_OPEN
        )

    def _make(self, **kwargs):
        return SupportTicketFactory(product=self.product, **kwargs)

    def _ids(self, qs):
        return set(qs.values_list("id", flat=True))

    def test_syncable_requires_usable_id_and_not_deleted(self):
        self.assertEqual(
            self._ids(SupportTicket.objects.syncable()),
            {self.live_open.id, self.live_solved.id, self.closed.id, self.no_status.id},
        )

    def test_active_includes_active_statuses_regardless_of_id(self):
        self.assertEqual(
            self._ids(SupportTicket.objects.active()),
            {self.live_open.id, self.null_id_open.id, self.blank_id_open.id},
        )

    def test_solved_includes_solved_and_closed(self):
        self.assertEqual(
            self._ids(SupportTicket.objects.solved()),
            {self.live_solved.id, self.closed.id},
        )

    def test_active_and_solved_exclude_deleted(self):
        self.assertNotIn(self.deleted_open.id, self._ids(SupportTicket.objects.active()))
        self.assertNotIn(self.deleted_open.id, self._ids(SupportTicket.objects.solved()))

    def test_active_syncable_composition_drops_unsyncable(self):
        # The sync dispatch path: active by status AND sync-eligible.
        self.assertEqual(
            self._ids(SupportTicket.objects.active().syncable()),
            {self.live_open.id},
        )
