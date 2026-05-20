from django.utils import timezone

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase


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


class PermittedZdStatusTargetsTests(TestCase):
    """Tests for SupportTicket.permitted_zd_status_targets() — the owner-facing
    state machine that decides which status-change actions are available.
    """

    def _ticket(self, zd_status, **extra):
        return SupportTicketFactory(zd_status=zd_status, **extra)

    def test_open_allows_solve(self):
        ticket = self._ticket(SupportTicket.ZD_STATUS_OPEN)
        self.assertEqual({SupportTicket.ZD_STATUS_SOLVED}, ticket.permitted_zd_status_targets())

    def test_pending_allows_solve(self):
        ticket = self._ticket(SupportTicket.ZD_STATUS_PENDING)
        self.assertEqual({SupportTicket.ZD_STATUS_SOLVED}, ticket.permitted_zd_status_targets())

    def test_waiting_allows_solve(self):
        ticket = self._ticket(SupportTicket.ZD_STATUS_WAITING)
        self.assertEqual({SupportTicket.ZD_STATUS_SOLVED}, ticket.permitted_zd_status_targets())

    def test_solved_allows_reopen_only(self):
        ticket = self._ticket(SupportTicket.ZD_STATUS_SOLVED)
        self.assertEqual({SupportTicket.ZD_STATUS_OPEN}, ticket.permitted_zd_status_targets())

    def test_closed_allows_nothing(self):
        ticket = self._ticket(SupportTicket.ZD_STATUS_CLOSED)
        self.assertEqual(set(), ticket.permitted_zd_status_targets())

    def test_null_zd_status_allows_nothing(self):
        ticket = self._ticket(None)
        self.assertEqual(set(), ticket.permitted_zd_status_targets())

    def test_non_sent_submission_allows_nothing(self):
        """Tickets that haven't reached Zendesk yet shouldn't expose status actions."""
        ticket = self._ticket(
            SupportTicket.ZD_STATUS_OPEN,
            submission_status=SupportTicket.STATUS_PENDING,
        )
        self.assertEqual(set(), ticket.permitted_zd_status_targets())

    def test_pending_status_change_blocks_actions(self):
        ticket = self._ticket(SupportTicket.ZD_STATUS_OPEN)
        ticket.pending_changes["zd_status"] = {
            "target_status": SupportTicket.ZD_STATUS_SOLVED,
            "status": "sending",
            "created_at": timezone.now().isoformat(),
            "last_attempted_at": timezone.now().isoformat(),
        }
        ticket.save(update_fields=["pending_changes"])
        self.assertEqual(set(), ticket.permitted_zd_status_targets())

    def test_failed_status_change_does_not_block_actions(self):
        """Failed pending entries shouldn't lock the user out of trying again."""
        ticket = self._ticket(SupportTicket.ZD_STATUS_OPEN)
        ticket.pending_changes["zd_status"] = {
            "target_status": SupportTicket.ZD_STATUS_SOLVED,
            "status": "failed",
            "allow_retries": True,
            "created_at": timezone.now().isoformat(),
            "last_attempted_at": timezone.now().isoformat(),
        }
        ticket.save(update_fields=["pending_changes"])
        self.assertEqual({SupportTicket.ZD_STATUS_SOLVED}, ticket.permitted_zd_status_targets())


class EffectivePendingStaleCoercionTests(TestCase):
    """Tests for the `created_at` fallback in `effective_pending(kind)`.

    Covers the case where a task never recorded an attempt (worker crashed,
    broker outage) — without the fallback, the UI would spin forever instead
    of recovering into a retryable failed state.
    """

    def _ticket_with_pending(self, kind, created_at, last_attempted_at=None):
        ticket = SupportTicketFactory(zd_status=SupportTicket.ZD_STATUS_OPEN)
        ticket.pending_changes[kind] = {
            "target_status": SupportTicket.ZD_STATUS_SOLVED,
            "status": "sending",
            "created_at": created_at,
            "last_attempted_at": last_attempted_at,
        }
        ticket.save(update_fields=["pending_changes"])
        return ticket

    def test_recent_created_at_no_attempt_returns_sending(self):
        ticket = self._ticket_with_pending("zd_status", created_at=timezone.now().isoformat())
        pending = ticket.effective_pending("zd_status")
        self.assertEqual("sending", pending["status"])

    def test_stale_created_at_no_attempt_coerces_to_failed(self):
        from datetime import timedelta as _td

        stale = (timezone.now() - _td(seconds=120)).isoformat()
        ticket = self._ticket_with_pending("zd_status", created_at=stale)
        pending = ticket.effective_pending("zd_status")
        self.assertEqual("failed", pending["status"])
        self.assertTrue(pending["allow_retries"])

    def test_recent_attempt_overrides_stale_created_at(self):
        from datetime import timedelta as _td

        stale = (timezone.now() - _td(seconds=300)).isoformat()
        ticket = self._ticket_with_pending(
            "zd_status",
            created_at=stale,
            last_attempted_at=timezone.now().isoformat(),
        )
        pending = ticket.effective_pending("zd_status")
        self.assertEqual("sending", pending["status"])

    def test_no_kind_returns_none(self):
        ticket = SupportTicketFactory()
        self.assertIsNone(ticket.effective_pending("zd_status"))
