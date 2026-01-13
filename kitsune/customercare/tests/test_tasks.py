from unittest.mock import patch

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tasks import (
    process_failed_zendesk_tickets,
    zendesk_submission_classifier,
)
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.llm.support.classifiers import classify_zendesk_submission
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    ZendeskConfigFactory,
)
from kitsune.sumo.tests import TestCase


class ZendeskSubmissionClassifierTests(TestCase):
    """Tests for zendesk_submission_classifier task."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="firefox", title="Firefox")
        self.zendesk_config = ZendeskConfigFactory(name="Test Config")
        self.support_config = ProductSupportConfigFactory(
            product=self.product,
            is_active=True,
            zendesk_config=self.zendesk_config
        )

    @patch("kitsune.customercare.tasks.classify_zendesk_submission")
    @patch("kitsune.customercare.tasks.process_zendesk_classification_result")
    def test_successful_classification(self, mock_process, mock_classify):
        """Test normal successful classification flow."""
        mock_classify.return_value = {
            "action": ModerationAction.NOT_SPAM,
            "spam_result": {},
            "product_result": {},
            "topic_result": {},
        }

        submission = SupportTicket.objects.create(
            subject="Help",
            description="Need help",
            category="general",
            email="user@example.com",
            product=self.product,
            status=SupportTicket.STATUS_PENDING
        )

        zendesk_submission_classifier(submission.id)

        mock_classify.assert_called_once_with(submission)
        mock_process.assert_called_once()

    def test_nonexistent_submission(self):
        """Test task handles nonexistent submission gracefully."""
        zendesk_submission_classifier(99999)

    @patch("kitsune.customercare.tasks.classify_zendesk_submission")
    @patch("kitsune.customercare.tasks.process_zendesk_classification_result")
    def test_classification_failure_marks_status(
        self, mock_process, mock_classify
    ):
        """Test that failed classification marks ticket as STATUS_PROCESSING_FAILED."""
        mock_classify.side_effect = Exception("LLM service unavailable")

        submission = SupportTicket.objects.create(
            subject="Help",
            description="Need help",
            category="general",
            email="user@example.com",
            product=self.product,
            status=SupportTicket.STATUS_PENDING
        )

        try:
            zendesk_submission_classifier(submission.id)
        except Exception:
            pass

        submission.refresh_from_db()
        self.assertEqual(submission.status, SupportTicket.STATUS_PROCESSING_FAILED)

    @patch("kitsune.llm.support.classifiers._handle_product_reassignment")
    @patch("kitsune.llm.support.classifiers.get_taxonomy")
    @patch("kitsune.llm.support.classifiers.classify_spam")
    @patch("kitsune.llm.support.classifiers.classify_topic")
    def test_skip_spam_moderation_enabled(self, mock_classify_topic, mock_classify_spam, mock_get_taxonomy, mock_reassignment):
        """Test that spam check is skipped when skip_spam_moderation=True."""
        self.zendesk_config.skip_spam_moderation = True
        self.zendesk_config.save()

        mock_get_taxonomy.return_value = {}
        mock_reassignment.return_value = None
        mock_classify_topic.return_value = {
            "topic_result": {"topic": "General Support", "confidence": 0.9}
        }

        submission = SupportTicket.objects.create(
            subject="Need help with deployment",
            description="How do I deploy Firefox Enterprise?",
            category="deployment",
            email="admin@enterprise.com",
            product=self.product,
            status=SupportTicket.STATUS_PENDING
        )

        result = classify_zendesk_submission(submission)

        mock_classify_spam.assert_not_called()
        mock_classify_topic.assert_called_once()
        self.assertEqual(result["action"], ModerationAction.NOT_SPAM)
        self.assertEqual(result["spam_result"], {})
        self.assertIn("topic_result", result)

    @patch("kitsune.llm.support.classifiers._handle_product_reassignment")
    @patch("kitsune.llm.support.classifiers.get_taxonomy")
    @patch("kitsune.llm.support.classifiers.classify_spam")
    @patch("kitsune.llm.support.classifiers.classify_topic")
    def test_skip_spam_moderation_disabled(self, mock_classify_topic, mock_classify_spam, mock_get_taxonomy, mock_reassignment):
        """Test that spam check runs normally when skip_spam_moderation=False."""
        self.zendesk_config.skip_spam_moderation = False
        self.zendesk_config.save()

        mock_get_taxonomy.return_value = {}
        mock_reassignment.return_value = None
        mock_classify_spam.return_value = {
            "spam_result": {"is_spam": False, "confidence": 0.1, "reason": ""}
        }
        mock_classify_topic.return_value = {
            "topic_result": {"topic": "General Support", "confidence": 0.9}
        }

        submission = SupportTicket.objects.create(
            subject="Need help",
            description="How do I use Firefox?",
            category="general",
            email="user@example.com",
            product=self.product,
            status=SupportTicket.STATUS_PENDING
        )

        classify_zendesk_submission(submission)

        mock_classify_spam.assert_called_once()
        mock_classify_topic.assert_called_once()


class ProcessFailedZendeskTicketsTests(TestCase):
    """Tests for process_failed_zendesk_tickets periodic task."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="firefox", title="Firefox")
        self.zendesk_config = ZendeskConfigFactory(name="Test Config")
        self.support_config = ProductSupportConfigFactory(
            product=self.product,
            is_active=True,
            zendesk_config=self.zendesk_config
        )

    @patch("kitsune.customercare.utils.send_support_ticket_to_zendesk")
    def test_process_failed_tickets(self, mock_send):
        """Test that periodic task processes failed tickets."""
        mock_send.return_value = True

        submission = SupportTicket.objects.create(
            subject="Help",
            description="Need help",
            category="general",
            email="user@example.com",
            product=self.product,
            status=SupportTicket.STATUS_PROCESSING_FAILED
        )

        process_failed_zendesk_tickets()

        mock_send.assert_called_once_with(submission)

    @patch("kitsune.customercare.utils.send_support_ticket_to_zendesk")
    def test_process_failed_tickets_ignores_other_statuses(self, mock_send):
        """Test that periodic task only processes STATUS_PROCESSING_FAILED tickets."""
        mock_send.return_value = True

        SupportTicket.objects.create(
            subject="Pending",
            description="Pending ticket",
            category="general",
            email="user@example.com",
            product=self.product,
            status=SupportTicket.STATUS_PENDING
        )
        SupportTicket.objects.create(
            subject="Sent",
            description="Sent ticket",
            category="general",
            email="user@example.com",
            product=self.product,
            status=SupportTicket.STATUS_SENT
        )

        process_failed_zendesk_tickets()

        mock_send.assert_not_called()

    @patch("kitsune.customercare.utils.send_support_ticket_to_zendesk")
    def test_process_failed_tickets_handles_send_failure(self, mock_send):
        """Test that periodic task handles cases where Zendesk send fails."""
        mock_send.return_value = False

        submission = SupportTicket.objects.create(
            subject="Help",
            description="Need help",
            category="general",
            email="user@example.com",
            product=self.product,
            status=SupportTicket.STATUS_PROCESSING_FAILED
        )

        process_failed_zendesk_tickets()

        mock_send.assert_called_once_with(submission)

        submission.refresh_from_db()
        self.assertEqual(submission.status, SupportTicket.STATUS_PROCESSING_FAILED)
