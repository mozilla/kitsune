from kitsune.customercare.models import SupportTicket, SupportTicketReplyOutbox
from kitsune.customercare.tests import SupportTicketFactory, SupportTicketReplyOutboxFactory
from kitsune.products.tests import ProductFactory
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


class SupportTicketReplyOutboxTests(TestCase):
    """Tests for SupportTicketReplyOutbox model + manager."""

    def setUp(self):
        self.ticket = SupportTicketFactory()

    def test_defaults(self):
        outbox = SupportTicketReplyOutboxFactory(ticket=self.ticket)
        self.assertEqual(outbox.status, SupportTicketReplyOutbox.STATUS_PENDING)
        self.assertEqual(outbox.attempt_count, 0)
        self.assertEqual(outbox.error_reason, "")
        self.assertIsNone(outbox.zendesk_comment_id)
        self.assertIsNone(outbox.posted_at)

    def test_ordering_by_created_at_asc(self):
        a = SupportTicketReplyOutboxFactory(ticket=self.ticket)
        b = SupportTicketReplyOutboxFactory(ticket=self.ticket)
        ordered = list(SupportTicketReplyOutbox.objects.filter(ticket=self.ticket))
        self.assertEqual(ordered, [a, b])

    def test_unconfirmed_for_returns_all_when_comments_empty(self):
        self.ticket.comments = []
        self.ticket.save(update_fields=["comments"])
        pending = SupportTicketReplyOutboxFactory(ticket=self.ticket)
        posted = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=42,
        )
        failed = SupportTicketReplyOutboxFactory(
            ticket=self.ticket, status=SupportTicketReplyOutbox.STATUS_FAILED
        )
        result = list(SupportTicketReplyOutbox.objects.unconfirmed_for(self.ticket))
        self.assertEqual(result, [pending, posted, failed])

    def test_unconfirmed_for_excludes_posted_when_id_in_mirror(self):
        self.ticket.comments = [{"id": 42, "body": "hi", "public": True}]
        self.ticket.save(update_fields=["comments"])
        posted_in_mirror = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=42,
        )
        posted_not_yet = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=99,
        )
        result = list(SupportTicketReplyOutbox.objects.unconfirmed_for(self.ticket))
        self.assertNotIn(posted_in_mirror, result)
        self.assertIn(posted_not_yet, result)

    def test_unconfirmed_for_keeps_pending_and_failed_regardless(self):
        """Pending rows have no zendesk_comment_id; failed rows may or may not — both stay."""
        self.ticket.comments = [{"id": 42, "body": "hi", "public": True}]
        self.ticket.save(update_fields=["comments"])
        pending = SupportTicketReplyOutboxFactory(ticket=self.ticket)
        failed_no_id = SupportTicketReplyOutboxFactory(
            ticket=self.ticket, status=SupportTicketReplyOutbox.STATUS_FAILED
        )
        result = list(SupportTicketReplyOutbox.objects.unconfirmed_for(self.ticket))
        self.assertIn(pending, result)
        self.assertIn(failed_no_id, result)

    def test_unconfirmed_for_scoped_to_ticket(self):
        other_ticket = SupportTicketFactory()
        mine = SupportTicketReplyOutboxFactory(ticket=self.ticket)
        SupportTicketReplyOutboxFactory(ticket=other_ticket)
        result = list(SupportTicketReplyOutbox.objects.unconfirmed_for(self.ticket))
        self.assertEqual(result, [mine])

    def test_cascade_delete_with_ticket(self):
        outbox = SupportTicketReplyOutboxFactory(ticket=self.ticket)
        self.ticket.delete()
        self.assertFalse(SupportTicketReplyOutbox.objects.filter(id=outbox.id).exists())

    def test_set_null_on_author_delete(self):
        author = UserFactory()
        outbox = SupportTicketReplyOutboxFactory(ticket=self.ticket, author=author)
        author.delete()
        outbox.refresh_from_db()
        self.assertIsNone(outbox.author)
