from django.contrib.auth.models import AnonymousUser, Group
from django.utils import timezone

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.groups.models import GroupProfile
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    ZendeskConfigFactory,
)
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
    """
    Tree layout:
        firefox-enterprise (root, not org)
        ├── company1   (org root)
        │   ├── company1.IT
        │   └── company1.marketing
        ├── company2   (org root)
        └── company3   (no org)
    """

    def setUp(self):
        self.product = ProductFactory()
        zd_config = ZendeskConfigFactory(name="prod-zd")
        self.support_config = ProductSupportConfigFactory(
            product=self.product, zendesk_config=zd_config
        )

        root_group = Group.objects.create(name="firefox-enterprise")
        self.root = GroupProfile.add_root(group=root_group, slug="firefox-enterprise")

        c1_group = Group.objects.create(name="company1")
        self.c1 = self.root.add_child(group=c1_group, slug="company1")
        self.support_config.hybrid_support_groups.add(c1_group)

        c2_group = Group.objects.create(name="company2")
        self.c2 = self.root.add_child(group=c2_group, slug="company2")
        self.support_config.hybrid_support_groups.add(c2_group)

        c3_group = Group.objects.create(name="company3")
        self.c3 = self.root.add_child(group=c3_group, slug="company3")

        it_group = Group.objects.create(name="company1.IT")
        self.c1_it = self.c1.add_child(group=it_group, slug="company1-it")
        mkt_group = Group.objects.create(name="company1.marketing")
        self.c1_mkt = self.c1.add_child(group=mkt_group, slug="company1-marketing")

        self.alice = UserFactory(username="alice")  # in company1.IT
        self.alice.groups.add(it_group)
        self.bob = UserFactory(username="bob")  # in company1.marketing
        self.bob.groups.add(mkt_group)
        self.carol = UserFactory(username="carol")  # in company2
        self.carol.groups.add(c2_group)
        self.dave = UserFactory(username="dave")  # no enterprise group
        self.mallory = UserFactory(username="mallory")  # root moderator
        self.root.leaders.add(self.mallory)

        self.alice_ticket = SupportTicketFactory(
            user=self.alice, product=self.product, org_group=self.c1
        )
        self.bob_ticket = SupportTicketFactory(
            user=self.bob, product=self.product, org_group=self.c1
        )
        self.carol_ticket = SupportTicketFactory(
            user=self.carol, product=self.product, org_group=self.c2
        )
        self.dave_ticket = SupportTicketFactory(user=self.dave, product=self.product)

    def test_anonymous_sees_nothing(self):
        self.assertFalse(SupportTicket.objects.accessible_to(AnonymousUser()).exists())

    def test_none_user_sees_nothing(self):
        self.assertFalse(SupportTicket.objects.accessible_to(None).exists())

    def test_staff_sees_everything(self):
        staff = UserFactory(is_staff=True)
        accessible = set(SupportTicket.objects.accessible_to(staff).values_list("id", flat=True))
        self.assertEqual(
            accessible,
            {self.alice_ticket.id, self.bob_ticket.id, self.carol_ticket.id, self.dave_ticket.id},
        )

    def test_member_sees_own_and_subtree_tickets(self):
        """alice (company1.IT) sees her own + bob's (company1.marketing) via company1 org."""
        accessible = set(
            SupportTicket.objects.accessible_to(self.alice).values_list("id", flat=True)
        )
        self.assertEqual(accessible, {self.alice_ticket.id, self.bob_ticket.id})

    def test_member_does_not_see_other_company(self):
        """alice (company1) cannot see carol's (company2) ticket."""
        accessible = set(
            SupportTicket.objects.accessible_to(self.alice).values_list("id", flat=True)
        )
        self.assertNotIn(self.carol_ticket.id, accessible)

    def test_non_org_user_sees_only_own(self):
        accessible = set(
            SupportTicket.objects.accessible_to(self.dave).values_list("id", flat=True)
        )
        self.assertEqual(accessible, {self.dave_ticket.id})

    def test_root_moderator_sees_all_orgs(self):
        """firefox-enterprise leader sees company1 + company2 tickets via moderation."""
        accessible = set(
            SupportTicket.objects.accessible_to(self.mallory).values_list("id", flat=True)
        )
        self.assertIn(self.alice_ticket.id, accessible)
        self.assertIn(self.bob_ticket.id, accessible)
        self.assertIn(self.carol_ticket.id, accessible)
        # personal ticket from non-org user is NOT moderated by mallory
        self.assertNotIn(self.dave_ticket.id, accessible)

    def test_subtree_teammate_can_view_but_cannot_reply(self):
        """bob can view alice's ticket via the company1 org, but only alice may reply."""
        self.assertIn(
            self.alice_ticket.id,
            SupportTicket.objects.accessible_to(self.bob).values_list("id", flat=True),
        )
        self.assertTrue(self.alice_ticket.can_reply(self.alice))
        self.assertFalse(self.alice_ticket.can_reply(self.bob))

    def test_root_moderator_cannot_reply(self):
        """Moderation grants visibility, not the right to reply as the owner."""
        self.assertFalse(self.alice_ticket.can_reply(self.mallory))

    def test_anonymous_cannot_reply(self):
        self.assertFalse(self.alice_ticket.can_reply(AnonymousUser()))
        self.assertFalse(self.alice_ticket.can_reply(None))
