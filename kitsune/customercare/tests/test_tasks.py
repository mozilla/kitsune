from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests
from zenpy.lib.api_objects import Comment
from zenpy.lib.exception import APIException

from kitsune.customercare.models import SupportTicket, SupportTicketReplyOutbox
from kitsune.customercare.tasks import (
    post_outbox_reply,
    process_failed_zendesk_tickets,
    process_zendesk_update,
    zendesk_submission_classifier,
)
from kitsune.customercare.tests import SupportTicketFactory, SupportTicketReplyOutboxFactory
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

    def _payload(self, event_type, event, *, ticket_id="12345", updated_at):
        return {
            "type": event_type,
            "detail": {"id": ticket_id, "updated_at": updated_at},
            "event": event,
        }

    def test_status_changed(self):
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.status_changed",
                {"current": "solved", "previous": "open"},
                updated_at="2026-03-24T10:30:00Z",
            )
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.comments, [])
        self.assertEqual(self.ticket.zd_status, "solved")
        self.assertEqual(str(self.ticket.zd_updated_at), "2026-03-24 10:30:00+00:00")

    def test_subject_changed(self):
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.subject_changed",
                {"current": "New subject", "previous": "Help"},
                updated_at="2026-03-24T10:30:00Z",
            )
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.subject, "New subject")

    def test_description_changed(self):
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.description_changed",
                {"current": "Updated description", "previous": "Need help"},
                updated_at="2026-03-24T10:30:00Z",
            )
        )
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.description, "Updated description")

    def test_comment_added(self):
        comment = {
            "id": 999,
            "body": "hey paul",
            "is_public": True,
            "author": {"id": 1, "is_staff": False, "name": "ringo"},
        }
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.comment_added",
                {"comment": comment},
                updated_at="2026-03-25T10:30:00Z",
            )
        )
        self.ticket.refresh_from_db()
        self.assertEqual(len(self.ticket.comments), 1)
        stored = self.ticket.comments[0]
        self.assertEqual(stored["body"], "hey paul")
        self.assertEqual(stored["author"]["name"], "ringo")
        self.assertEqual(stored["created_at"], "2026-03-25T10:30:00Z")
        self.assertTrue(stored["public"])
        self.assertNotIn("is_public", stored)
        self.assertEqual(str(self.ticket.zd_updated_at), "2026-03-25 10:30:00+00:00")

    def test_comment_added_defaults_public_false_when_missing(self):
        """A comment without is_public should be stored with public=False."""
        comment = {"id": 1, "body": "hi", "author": {"name": "ringo"}}
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.comment_added",
                {"comment": comment},
                updated_at="2026-03-25T10:30:00Z",
            )
        )
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.comments[0]["public"])

    def test_appends_multiple_comments(self):
        """Successive comment_added events append to the comments list."""
        comment1 = {"id": 1, "body": "First reply", "author": {"name": "ringo"}}
        comment2 = {"id": 2, "body": "Second reply", "author": {"name": "paul"}}
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.comment_added",
                {"comment": comment1},
                updated_at="2026-03-26T10:30:00Z",
            )
        )
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.comment_added",
                {"comment": comment2},
                updated_at="2026-03-26T10:35:00Z",
            )
        )
        self.ticket.refresh_from_db()
        self.assertEqual(len(self.ticket.comments), 2)
        self.assertEqual(self.ticket.comments[0]["body"], "First reply")
        self.assertEqual(self.ticket.comments[0]["created_at"], "2026-03-26T10:30:00Z")
        self.assertEqual(self.ticket.comments[1]["body"], "Second reply")
        self.assertEqual(self.ticket.comments[1]["created_at"], "2026-03-26T10:35:00Z")
        self.assertEqual(str(self.ticket.zd_updated_at), "2026-03-26 10:35:00+00:00")

    def test_unhandled_event_type_is_noop(self):
        """Event types we don't handle should be ignored without raising."""
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.priority_changed",
                {"current": "high", "previous": "normal"},
                updated_at="2026-03-24T10:30:00Z",
            )
        )
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.zd_updated_at)

    def test_no_matching_ticket_is_noop(self):
        """Webhook for a ticket not in our DB should not raise."""
        process_zendesk_update(
            self._payload(
                "zen:event-type:ticket.status_changed",
                {"current": "open"},
                ticket_id="99999",
                updated_at="2026-03-24T10:30:00Z",
            )
        )

    def test_missing_ticket_id_raises(self):
        """Payload without detail.id should raise ValueError so Sentry captures it."""
        with self.assertRaises(ValueError):
            process_zendesk_update(
                {
                    "type": "zen:event-type:ticket.status_changed",
                    "detail": {},
                    "event": {"current": "open"},
                }
            )

    def test_missing_updated_at_raises(self):
        """Payload without detail.updated_at should raise ValueError."""
        with self.assertRaises(ValueError):
            process_zendesk_update(
                {
                    "type": "zen:event-type:ticket.status_changed",
                    "detail": {"id": "12345"},
                    "event": {"current": "open"},
                }
            )
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.zd_status)
        self.assertIsNone(self.ticket.zd_updated_at)

    def test_missing_event_raises(self):
        """Payload without an event field should raise ValueError."""
        with self.assertRaises(ValueError):
            process_zendesk_update(
                {
                    "type": "zen:event-type:ticket.status_changed",
                    "detail": {"id": "12345", "updated_at": "2026-03-24T10:30:00Z"},
                }
            )
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.zd_updated_at)


def _build_audit(comment_id):
    """Build a fake TicketAudit whose events list contains one new Comment."""
    return SimpleNamespace(events=[Comment(id=comment_id, body="x", public=True)])


def _api_exc(status_code):
    """Build an APIException carrying a response with the given status code."""
    response = MagicMock(status_code=status_code)
    return APIException("zendesk", response=response)


class PostOutboxReplyTests(TestCase):
    """Tests for the post_outbox_reply task."""

    def setUp(self):
        self.ticket = SupportTicketFactory(
            zendesk_ticket_id="987",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )
        self.outbox = SupportTicketReplyOutboxFactory(ticket=self.ticket, body="hello support")

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_happy_path_marks_posted_and_stamps_id(self, MockClient):
        MockClient.return_value.add_ticket_comment.return_value = _build_audit(12345)
        post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_POSTED)
        self.assertEqual(self.outbox.zendesk_comment_id, 12345)
        self.assertIsNotNone(self.outbox.posted_at)

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_short_circuits_when_already_posted(self, MockClient):
        self.outbox.status = SupportTicketReplyOutbox.STATUS_POSTED
        self.outbox.zendesk_comment_id = 7
        self.outbox.save()
        post_outbox_reply(self.outbox.id)
        MockClient.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_short_circuits_when_already_failed(self, MockClient):
        self.outbox.status = SupportTicketReplyOutbox.STATUS_FAILED
        self.outbox.save()
        post_outbox_reply(self.outbox.id)
        MockClient.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_missing_outbox_id_returns_silently(self, MockClient):
        post_outbox_reply(99999)
        MockClient.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_author_none_marks_failed(self, MockClient):
        self.outbox.author = None
        self.outbox.save()
        post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_FAILED)
        self.assertIn("Author missing", self.outbox.error_reason)
        MockClient.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_no_zendesk_ticket_id_marks_failed(self, MockClient):
        self.ticket.zendesk_ticket_id = ""
        self.ticket.save()
        post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_FAILED)
        self.assertIn("no Zendesk id", self.outbox.error_reason)
        MockClient.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_empty_audit_events_marks_failed(self, MockClient):
        MockClient.return_value.add_ticket_comment.return_value = SimpleNamespace(events=[])
        post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_FAILED)
        self.assertIn("no comment id", self.outbox.error_reason)

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_transient_api_exception_reraises_and_increments(self, MockClient):
        MockClient.return_value.add_ticket_comment.side_effect = _api_exc(503)
        with self.assertRaises(APIException):
            post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_PENDING)
        self.assertEqual(self.outbox.attempt_count, 1)

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_transient_network_error_reraises_and_increments(self, MockClient):
        MockClient.return_value.add_ticket_comment.side_effect = (
            requests.exceptions.ConnectionError("boom")
        )
        with self.assertRaises(requests.exceptions.ConnectionError):
            post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_PENDING)
        self.assertEqual(self.outbox.attempt_count, 1)

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_permanent_api_exception_marks_failed_no_reraise(self, MockClient):
        MockClient.return_value.add_ticket_comment.side_effect = _api_exc(404)
        post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_FAILED)
        self.assertEqual(self.outbox.attempt_count, 1)
        self.assertIn("zendesk", self.outbox.error_reason)

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_value_error_marks_failed(self, MockClient):
        MockClient.return_value.add_ticket_comment.side_effect = ValueError("anon")
        post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_FAILED)
        self.assertIn("anon", self.outbox.error_reason)

    @patch("kitsune.customercare.tasks.ZendeskClient")
    def test_max_attempts_reached_marks_failed_on_transient(self, MockClient):
        self.outbox.attempt_count = 2
        self.outbox.save()
        MockClient.return_value.add_ticket_comment.side_effect = _api_exc(503)
        # Third attempt should mark failed and swallow.
        post_outbox_reply(self.outbox.id)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_FAILED)
        self.assertEqual(self.outbox.attempt_count, 3)


class CommentAddedCleanupTests(TestCase):
    """When process_zendesk_update appends a comment, matching `posted` outbox rows get deleted."""

    def setUp(self):
        self.ticket = SupportTicketFactory(zendesk_ticket_id="555")

    def _payload(self, comment_id, is_public=True):
        return {
            "type": "zen:event-type:ticket.comment_added",
            "detail": {"id": "555", "updated_at": "2026-05-01T00:00:00Z"},
            "event": {
                "comment": {
                    "id": comment_id,
                    "body": "from zendesk",
                    "is_public": is_public,
                    "author": {"id": 1, "name": "agent"},
                }
            },
        }

    def test_deletes_matching_posted_row(self):
        row = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=777,
        )
        process_zendesk_update(self._payload(777))
        self.assertFalse(SupportTicketReplyOutbox.objects.filter(id=row.id).exists())

    def test_no_op_when_no_matching_row(self):
        row = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=111,
        )
        process_zendesk_update(self._payload(999))
        self.assertTrue(SupportTicketReplyOutbox.objects.filter(id=row.id).exists())

    def test_does_not_delete_pending_row_with_matching_id(self):
        """Pathological: a pending row with a matching id (shouldn't normally happen) is kept."""
        row = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_PENDING,
            zendesk_comment_id=777,
        )
        process_zendesk_update(self._payload(777))
        self.assertTrue(SupportTicketReplyOutbox.objects.filter(id=row.id).exists())

    def test_does_not_delete_failed_row_with_matching_id(self):
        row = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_FAILED,
            zendesk_comment_id=777,
        )
        process_zendesk_update(self._payload(777))
        self.assertTrue(SupportTicketReplyOutbox.objects.filter(id=row.id).exists())

    def test_non_comment_event_does_not_touch_outbox(self):
        row = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=777,
        )
        process_zendesk_update(
            {
                "type": "zen:event-type:ticket.status_changed",
                "detail": {"id": "555", "updated_at": "2026-05-01T00:00:00Z"},
                "event": {"current": "solved"},
            }
        )
        self.assertTrue(SupportTicketReplyOutbox.objects.filter(id=row.id).exists())
