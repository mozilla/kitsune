from unittest.mock import patch

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tasks import (
    process_failed_zendesk_tickets,
    process_zendesk_update,
    sync_active_support_tickets,
    sync_support_ticket,
    zendesk_submission_classifier,
)
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.llm.support.classifiers import classify_zendesk_submission
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    TopicFactory,
    ZendeskConfigFactory,
    ZendeskTopicFactory,
)
from kitsune.sumo.tests import TestCase


class ZendeskSubmissionClassifierTests(TestCase):
    """Tests for zendesk_submission_classifier task."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="firefox", title="Firefox")
        self.zendesk_config = ZendeskConfigFactory(name="Test Config")
        self.support_config = ProductSupportConfigFactory(
            product=self.product, is_active=True, zendesk_config=self.zendesk_config
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
            submission_status=SupportTicket.STATUS_PENDING,
        )

        zendesk_submission_classifier(submission.id)

        mock_classify.assert_called_once_with(submission)
        mock_process.assert_called_once()

    def test_nonexistent_submission(self):
        """Test task handles nonexistent submission gracefully."""
        zendesk_submission_classifier(99999)

    @patch("kitsune.customercare.tasks.classify_zendesk_submission")
    @patch("kitsune.customercare.tasks.process_zendesk_classification_result")
    def test_classification_failure_marks_status(self, mock_process, mock_classify):
        """Test that failed classification marks ticket as STATUS_PROCESSING_FAILED."""
        mock_classify.side_effect = Exception("LLM service unavailable")

        submission = SupportTicket.objects.create(
            subject="Help",
            description="Need help",
            category="general",
            email="user@example.com",
            product=self.product,
            submission_status=SupportTicket.STATUS_PENDING,
        )

        try:
            zendesk_submission_classifier(submission.id)
        except Exception:
            pass

        submission.refresh_from_db()
        self.assertEqual(submission.submission_status, SupportTicket.STATUS_PROCESSING_FAILED)

    @patch("kitsune.llm.support.classifiers._handle_product_reassignment")
    @patch("kitsune.llm.support.classifiers.get_taxonomy")
    @patch("kitsune.llm.support.classifiers.classify_spam")
    @patch("kitsune.llm.support.classifiers.classify_topic")
    def test_skip_spam_moderation_enabled(
        self, mock_classify_topic, mock_classify_spam, mock_get_taxonomy, mock_reassignment
    ):
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
            submission_status=SupportTicket.STATUS_PENDING,
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
    def test_skip_spam_moderation_disabled(
        self, mock_classify_topic, mock_classify_spam, mock_get_taxonomy, mock_reassignment
    ):
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
            submission_status=SupportTicket.STATUS_PENDING,
        )

        classify_zendesk_submission(submission)

        mock_classify_spam.assert_called_once()
        mock_classify_topic.assert_called_once()

    @patch("kitsune.llm.support.classifiers._handle_product_reassignment")
    @patch("kitsune.llm.support.classifiers.get_taxonomy")
    @patch("kitsune.llm.support.classifiers.classify_spam")
    @patch("kitsune.llm.support.classifiers.classify_topic")
    def test_form_selection_passed_as_topic_hint(
        self, mock_classify_topic, mock_classify_spam, mock_get_taxonomy, mock_reassignment
    ):
        """The selected topic's taxonomy title is passed to classify_topic as a hint."""
        mock_get_taxonomy.return_value = {}
        mock_reassignment.return_value = None
        mock_classify_spam.return_value = {"spam_result": {"is_spam": False}}
        mock_classify_topic.return_value = {"topic_result": {"topic": "Edit account details"}}

        topic = TopicFactory(title="Edit account details")
        ZendeskTopicFactory(slug="test-edit-account-topic", topic=topic)

        submission = SupportTicket.objects.create(
            subject="Change my email",
            description="I want to change the email on my account",
            category="test-edit-account-topic",
            email="user@example.com",
            product=self.product,
            submission_status=SupportTicket.STATUS_PENDING,
        )

        classify_zendesk_submission(submission)

        payload = mock_classify_topic.call_args.args[0]
        self.assertEqual(payload["selected_topic"], "Edit account details")

    @patch("kitsune.llm.support.classifiers._handle_product_reassignment")
    @patch("kitsune.llm.support.classifiers.get_taxonomy")
    @patch("kitsune.llm.support.classifiers.classify_spam")
    @patch("kitsune.llm.support.classifiers.classify_topic")
    def test_no_topic_hint_without_matching_selection(
        self, mock_classify_topic, mock_classify_spam, mock_get_taxonomy, mock_reassignment
    ):
        """No hint is passed when the category matches no ZendeskTopic."""
        mock_get_taxonomy.return_value = {}
        mock_reassignment.return_value = None
        mock_classify_spam.return_value = {"spam_result": {"is_spam": False}}
        mock_classify_topic.return_value = {"topic_result": {"topic": "General Support"}}

        submission = SupportTicket.objects.create(
            subject="Need help",
            description="How do I use Firefox?",
            category="unknown-category",
            email="user@example.com",
            product=self.product,
            submission_status=SupportTicket.STATUS_PENDING,
        )

        classify_zendesk_submission(submission)

        payload = mock_classify_topic.call_args.args[0]
        self.assertNotIn("selected_topic", payload)


class ProcessFailedZendeskTicketsTests(TestCase):
    """Tests for process_failed_zendesk_tickets periodic task."""

    def setUp(self):
        """Set up test data."""
        self.product = ProductFactory(slug="firefox", title="Firefox")
        self.zendesk_config = ZendeskConfigFactory(name="Test Config")
        self.support_config = ProductSupportConfigFactory(
            product=self.product, is_active=True, zendesk_config=self.zendesk_config
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
            submission_status=SupportTicket.STATUS_PROCESSING_FAILED,
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
            submission_status=SupportTicket.STATUS_PENDING,
        )
        SupportTicket.objects.create(
            subject="Sent",
            description="Sent ticket",
            category="general",
            email="user@example.com",
            product=self.product,
            submission_status=SupportTicket.STATUS_SENT,
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
            submission_status=SupportTicket.STATUS_PROCESSING_FAILED,
        )

        process_failed_zendesk_tickets()

        mock_send.assert_called_once_with(submission)

        submission.refresh_from_db()
        self.assertEqual(submission.submission_status, SupportTicket.STATUS_PROCESSING_FAILED)


class ProcessZendeskUpdateTests(TestCase):
    """Tests for process_zendesk_update Celery task."""

    def setUp(self):
        self.product = ProductFactory(slug="firefox", title="Firefox")
        self.ticket = SupportTicket.objects.create(
            subject="Help",
            description="Need help",
            category="general",
            email="user@example.com",
            product=self.product,
            submission_status=SupportTicket.STATUS_SENT,
            zendesk_ticket_id="12345",
        )

    def _payload(self, event_type, *, ticket_id="12345"):
        return {
            "type": event_type,
            "detail": {"id": ticket_id},
        }

    @patch("kitsune.customercare.tasks.apply_zendesk_ticket_data")
    @patch("kitsune.customercare.tasks.fetch_zendesk_ticket_data", return_value=(None, None))
    def test_status_changed_triggers_resync(self, mock_fetch, mock_apply):
        process_zendesk_update(self._payload("zen:event-type:ticket.status_changed"))

        mock_fetch.assert_called_once_with("12345")
        mock_apply.assert_called_once()
        self.assertEqual(mock_apply.call_args.args[0].id, self.ticket.id)

    @patch("kitsune.customercare.tasks.apply_zendesk_ticket_data")
    @patch("kitsune.customercare.tasks.fetch_zendesk_ticket_data", return_value=(None, None))
    def test_subject_changed_triggers_resync(self, mock_fetch, mock_apply):
        process_zendesk_update(self._payload("zen:event-type:ticket.subject_changed"))

        mock_fetch.assert_called_once_with("12345")
        mock_apply.assert_called_once()
        self.assertEqual(mock_apply.call_args.args[0].id, self.ticket.id)

    @patch("kitsune.customercare.tasks.apply_zendesk_ticket_data")
    @patch("kitsune.customercare.tasks.fetch_zendesk_ticket_data", return_value=(None, None))
    def test_description_changed_triggers_resync(self, mock_fetch, mock_apply):
        process_zendesk_update(self._payload("zen:event-type:ticket.description_changed"))

        mock_fetch.assert_called_once_with("12345")
        mock_apply.assert_called_once()
        self.assertEqual(mock_apply.call_args.args[0].id, self.ticket.id)

    @patch("kitsune.customercare.tasks.apply_zendesk_ticket_data")
    @patch("kitsune.customercare.tasks.fetch_zendesk_ticket_data", return_value=(None, None))
    def test_comment_added_triggers_resync(self, mock_fetch, mock_apply):
        process_zendesk_update(self._payload("zen:event-type:ticket.comment_added"))

        mock_fetch.assert_called_once_with("12345")
        mock_apply.assert_called_once()
        self.assertEqual(mock_apply.call_args.args[0].id, self.ticket.id)

    @patch("kitsune.customercare.tasks.apply_zendesk_ticket_data")
    @patch("kitsune.customercare.tasks.fetch_zendesk_ticket_data")
    def test_unhandled_event_type_is_noop(self, mock_fetch, mock_apply):
        process_zendesk_update(self._payload("zen:event-type:ticket.priority_changed"))

        mock_fetch.assert_not_called()
        mock_apply.assert_not_called()

    @patch("kitsune.customercare.tasks.apply_zendesk_ticket_data")
    @patch("kitsune.customercare.tasks.fetch_zendesk_ticket_data")
    def test_no_matching_ticket_is_noop(self, mock_fetch, mock_apply):
        process_zendesk_update(
            self._payload("zen:event-type:ticket.status_changed", ticket_id="99999")
        )

        mock_fetch.assert_not_called()
        mock_apply.assert_not_called()

    def test_missing_ticket_id_raises(self):
        """Payload without detail.id should raise ValueError so Sentry captures it."""
        with self.assertRaises(ValueError):
            process_zendesk_update(
                {
                    "type": "zen:event-type:ticket.status_changed",
                    "detail": {},
                }
            )


class SyncSupportTicketTests(TestCase):
    """Tests for the sync_support_ticket per-ticket task."""

    def setUp(self):
        self.product = ProductFactory(slug="firefox", title="Firefox")

    def _make_ticket(self, **overrides):
        defaults = {
            "subject": "Help",
            "description": "Need help",
            "category": "general",
            "email": "user@example.com",
            "product": self.product,
            "zendesk_ticket_id": "12345",
            "zd_status": SupportTicket.ZD_STATUS_OPEN,
        }
        defaults.update(overrides)
        return SupportTicket.objects.create(**defaults)

    @patch("kitsune.customercare.tasks.sync_ticket_from_zendesk")
    def test_calls_helper_with_loaded_ticket(self, mock_helper):
        ticket = self._make_ticket()

        sync_support_ticket(ticket.id)

        mock_helper.assert_called_once()
        called_ticket = mock_helper.call_args[0][0]
        self.assertEqual(called_ticket.id, ticket.id)

    @patch("kitsune.customercare.tasks.sync_ticket_from_zendesk")
    def test_missing_ticket_returns_silently(self, mock_helper):
        sync_support_ticket(999999)

        mock_helper.assert_not_called()

    @patch("kitsune.customercare.tasks.sync_ticket_from_zendesk")
    def test_null_or_blank_zendesk_ticket_id_skips_helper(self, mock_helper):
        null_ticket = self._make_ticket(zendesk_ticket_id=None)
        blank_ticket = self._make_ticket(zendesk_ticket_id="")

        sync_support_ticket(null_ticket.id)
        sync_support_ticket(blank_ticket.id)

        mock_helper.assert_not_called()

    @patch("kitsune.customercare.tasks.sync_ticket_from_zendesk")
    def test_helper_exception_propagates(self, mock_helper):
        mock_helper.side_effect = RuntimeError("Zendesk down")
        ticket = self._make_ticket()

        with self.assertRaises(RuntimeError):
            sync_support_ticket(ticket.id)


class SyncActiveSupportTicketsTests(TestCase):
    """Tests for the sync_active_support_tickets orchestrator task."""

    def setUp(self):
        self.product = ProductFactory(slug="firefox", title="Firefox")

    def _make_ticket(self, zd_status, zendesk_ticket_id="12345"):
        return SupportTicket.objects.create(
            product=self.product,
            zendesk_ticket_id=zendesk_ticket_id,
            zd_status=zd_status,
        )

    @patch("kitsune.customercare.tasks.sync_ticket_from_zendesk")
    def test_dispatches_only_active_tickets_with_zendesk_ids(self, mock_sync):
        active_new = self._make_ticket(SupportTicket.ZD_STATUS_NEW)
        active_open = self._make_ticket(SupportTicket.ZD_STATUS_OPEN)
        active_pending = self._make_ticket(SupportTicket.ZD_STATUS_PENDING)
        active_hold = self._make_ticket(SupportTicket.ZD_STATUS_HOLD)
        # Inactive statuses — should not be dispatched.
        self._make_ticket(SupportTicket.ZD_STATUS_SOLVED)
        self._make_ticket(SupportTicket.ZD_STATUS_CLOSED)
        # Active status but no Zendesk id — should not be dispatched.
        self._make_ticket(SupportTicket.ZD_STATUS_OPEN, zendesk_ticket_id="")

        sync_active_support_tickets()

        self.assertEqual(mock_sync.call_count, 4)
        dispatched_ids = {call.args[0].id for call in mock_sync.call_args_list}
        self.assertEqual(
            dispatched_ids,
            {active_new.id, active_open.id, active_pending.id, active_hold.id},
        )

    @patch("kitsune.customercare.tasks.sync_ticket_from_zendesk")
    def test_no_active_tickets_dispatches_nothing(self, mock_sync):
        self._make_ticket(SupportTicket.ZD_STATUS_SOLVED)
        self._make_ticket(SupportTicket.ZD_STATUS_CLOSED)

        sync_active_support_tickets()

        mock_sync.assert_not_called()
