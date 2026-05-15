from django.utils import timezone

from kitsune.customercare.models import SupportTicket
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
