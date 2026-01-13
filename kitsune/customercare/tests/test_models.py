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
        status_values = [choice[0] for choice in SupportTicket.STATUS_CHOICES]
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
            status=SupportTicket.STATUS_PROCESSING_FAILED
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, SupportTicket.STATUS_PROCESSING_FAILED)

    def test_default_status_is_pending(self):
        """Test that default status is STATUS_PENDING."""
        ticket = SupportTicket.objects.create(
            subject="Test",
            description="Test description",
            category="test",
            email="test@example.com",
            product=self.product
        )

        self.assertEqual(ticket.status, SupportTicket.STATUS_PENDING)

    def test_str_method(self):
        """Test the __str__ method includes status."""
        ticket = SupportTicket.objects.create(
            subject="Test Subject",
            description="Test description",
            category="test",
            email="test@example.com",
            product=self.product,
            status=SupportTicket.STATUS_PROCESSING_FAILED
        )

        str_repr = str(ticket)
        self.assertIn("Test Subject", str_repr)
        self.assertIn("processing_failed", str_repr)
