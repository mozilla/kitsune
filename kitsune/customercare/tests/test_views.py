import base64
import hashlib
import hmac
import json
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from zenpy.lib.exception import APIException

from kitsune.customercare.models import SupportTicket, SupportTicketReplyOutbox
from kitsune.customercare.tests import SupportTicketFactory, SupportTicketReplyOutboxFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory

WEBHOOK_API_KEY = "test-webhook-api-key"
WEBHOOK_SIGNING_SECRET = "test-webhook-secret"
WEBHOOK_URL = "/customercare/zendesk/updates"


def _sign_payload(body, timestamp="1234567890", secret=WEBHOOK_SIGNING_SECRET):
    """Generate a valid HMAC-SHA256 signature for the given payload."""
    message = timestamp.encode("utf-8") + body
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


@override_settings(
    ZENDESK_WEBHOOK_API_KEY=WEBHOOK_API_KEY,
    ZENDESK_WEBHOOK_SIGNING_SECRET=WEBHOOK_SIGNING_SECRET,
)
class ZendeskWebhookViewTests(TestCase):
    """Tests for ZendeskWebhookView authentication and request handling."""

    def _post(self, payload, signature=None, timestamp="1234567890", api_key=WEBHOOK_API_KEY):
        body = json.dumps(payload).encode("utf-8")
        if signature is None:
            signature = _sign_payload(body, timestamp)
        headers = {
            "HTTP_X_ZENDESK_WEBHOOK_SIGNATURE": signature,
            "HTTP_X_ZENDESK_WEBHOOK_SIGNATURE_TIMESTAMP": timestamp,
        }
        if api_key is not None:
            headers["HTTP_ZENDESK_WEBHOOK_API_KEY"] = api_key
        return self.client.post(
            WEBHOOK_URL,
            data=body,
            content_type="application/json",
            **headers,
        )

    def test_valid_request_returns_200(self):
        response = self._post({"ticket_id": "123", "status": "open"})
        self.assertEqual(response.status_code, 200)

    def test_missing_api_key_returns_403(self):
        response = self._post({"ticket_id": "123"}, api_key=None)
        self.assertEqual(response.status_code, 403)

    def test_invalid_api_key_returns_403(self):
        response = self._post({"ticket_id": "123"}, api_key="wrong-key")
        self.assertEqual(response.status_code, 403)

    def test_missing_signature_returns_403(self):
        body = json.dumps({"ticket_id": "123"}).encode("utf-8")
        response = self.client.post(
            WEBHOOK_URL,
            data=body,
            content_type="application/json",
            HTTP_ZENDESK_WEBHOOK_API_KEY=WEBHOOK_API_KEY,
        )
        self.assertEqual(response.status_code, 403)

    def test_missing_timestamp_returns_403(self):
        body = json.dumps({"ticket_id": "123"}).encode("utf-8")
        signature = _sign_payload(body)
        response = self.client.post(
            WEBHOOK_URL,
            data=body,
            content_type="application/json",
            HTTP_ZENDESK_WEBHOOK_API_KEY=WEBHOOK_API_KEY,
            HTTP_X_ZENDESK_WEBHOOK_SIGNATURE=signature,
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_signature_returns_403(self):
        response = self._post(
            {"ticket_id": "123"},
            signature=base64.b64encode(b"invalid").decode("utf-8"),
        )
        self.assertEqual(response.status_code, 403)

    def test_malformed_signature_returns_403(self):
        """Non-base64 signature header should produce 403, not 500."""
        response = self._post({"ticket_id": "123"}, signature="this is malformed")
        self.assertEqual(response.status_code, 403)

    def test_invalid_json_returns_400(self):
        body = b"not json"
        signature = _sign_payload(body)
        response = self.client.post(
            WEBHOOK_URL,
            data=body,
            content_type="application/json",
            HTTP_ZENDESK_WEBHOOK_API_KEY=WEBHOOK_API_KEY,
            HTTP_X_ZENDESK_WEBHOOK_SIGNATURE=signature,
            HTTP_X_ZENDESK_WEBHOOK_SIGNATURE_TIMESTAMP="1234567890",
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_payload_returns_400(self):
        response = self._post({})
        self.assertEqual(response.status_code, 400)

    def test_get_method_not_allowed(self):
        response = self.client.get(WEBHOOK_URL)
        self.assertEqual(response.status_code, 405)


class TicketDetailViewTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.other = UserFactory()
        self.ticket = SupportTicketFactory(user=self.owner)

    def test_owner_can_view(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertEqual(200, response.status_code)

    def test_other_user_gets_404(self):
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertEqual(404, response.status_code)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertEqual(302, response.status_code)
        self.assertIn("/users/login", response["Location"])

    def test_staff_can_view_any_ticket(self):
        staff = UserFactory()
        perm = Permission.objects.get(codename="change_supportticket")
        staff.user_permissions.add(perm)
        self.client.force_login(staff)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertEqual(200, response.status_code)

    def test_get_absolute_url(self):
        expected = reverse(
            "customercare.ticket_detail", args=[self.owner.username, self.ticket.id]
        )
        self.assertEqual(expected, self.ticket.get_absolute_url())

    def test_template_shows_subject(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertContains(response, self.ticket.subject)

    def test_template_shows_description(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertContains(response, self.ticket.description)

    def test_template_shows_status_badge(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertContains(response, 'class="status-label')


class SyncTicketCommentsViewTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.other = UserFactory()
        self.ticket = SupportTicketFactory(user=self.owner, zendesk_ticket_id="123")

    def _url(self):
        return reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])

    def _htmx_get(self):
        return self.client.get(self._url(), HTTP_HX_REQUEST="true")

    @patch("kitsune.customercare.views.sync_ticket_from_zendesk")
    def test_htmx_request_triggers_sync_and_returns_partial(self, mock_sync):
        self.client.force_login(self.owner)
        response = self._htmx_get()
        self.assertEqual(200, response.status_code)
        mock_sync.assert_called_once_with(self.ticket)

    @patch("kitsune.customercare.views.sync_ticket_from_zendesk")
    def test_zd_failure_returns_error_partial(self, mock_sync):
        mock_sync.side_effect = APIException("ZD unreachable")
        self.client.force_login(self.owner)
        response = self._htmx_get()
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "latest replies")

    def test_non_owner_htmx_gets_404(self):
        self.client.force_login(self.other)
        response = self._htmx_get()
        self.assertEqual(404, response.status_code)

    def test_anonymous_htmx_redirects(self):
        response = self._htmx_get()
        self.assertEqual(302, response.status_code)


class TicketReplyPostTests(TestCase):
    """POST to ticket_detail submits a reply via the outbox."""

    def setUp(self):
        self.owner = UserFactory()
        self.other = UserFactory()
        self.ticket = SupportTicketFactory(
            user=self.owner,
            zendesk_ticket_id="987",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )

    def _url(self):
        return reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_owner_post_creates_outbox_and_dispatches(self, mock_delay):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "thanks!"})
        self.assertEqual(302, response.status_code)
        outbox = SupportTicketReplyOutbox.objects.get(ticket=self.ticket)
        self.assertEqual(outbox.author, self.owner)
        self.assertEqual(outbox.body, "thanks!")
        self.assertEqual(outbox.status, SupportTicketReplyOutbox.STATUS_PENDING)
        mock_delay.assert_called_once_with(outbox.id)

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_htmx_post_returns_partial(self, mock_delay):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "hi there"}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "hi there")
        self.assertContains(response, 'id="thread-replies"')

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_non_owner_post_404(self, mock_delay):
        """Non-owner without staff perm hits the existing owner-or-perm gate → 404."""
        self.client.force_login(self.other)
        response = self.client.post(self._url(), data={"body": "evil"})
        self.assertEqual(404, response.status_code)
        self.assertFalse(SupportTicketReplyOutbox.objects.exists())
        mock_delay.assert_not_called()

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_staff_with_perm_post_forbidden(self, mock_delay):
        staff = UserFactory()
        perm = Permission.objects.get(codename="change_supportticket")
        staff.user_permissions.add(perm)
        self.client.force_login(staff)
        response = self.client.post(self._url(), data={"body": "trying"})
        self.assertEqual(403, response.status_code)
        self.assertFalse(SupportTicketReplyOutbox.objects.exists())
        mock_delay.assert_not_called()

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_post_rejected_when_solved(self, mock_delay):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_SOLVED
        self.ticket.save()
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "hi"})
        self.assertEqual(400, response.status_code)
        self.assertFalse(SupportTicketReplyOutbox.objects.exists())
        mock_delay.assert_not_called()

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_post_rejected_when_closed(self, mock_delay):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_CLOSED
        self.ticket.save()
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "hi"})
        self.assertEqual(400, response.status_code)

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_empty_body_invalid(self, mock_delay):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": ""}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertFalse(SupportTicketReplyOutbox.objects.exists())
        mock_delay.assert_not_called()

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_whitespace_only_body_invalid(self, mock_delay):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "   \n  "}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertFalse(SupportTicketReplyOutbox.objects.exists())

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_oversized_body_invalid(self, mock_delay):
        self.client.force_login(self.owner)
        body = "x" * (SupportTicketReplyOutbox.BODY_MAX_LENGTH + 1)
        response = self.client.post(self._url(), data={"body": body}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertFalse(SupportTicketReplyOutbox.objects.exists())

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_post_strips_whitespace(self, mock_delay):
        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "  hello!  "})
        outbox = SupportTicketReplyOutbox.objects.get(ticket=self.ticket)
        self.assertEqual(outbox.body, "hello!")

    def test_anonymous_post_redirects(self):
        response = self.client.post(self._url(), data={"body": "hi"})
        self.assertEqual(302, response.status_code)


class RetryOutboxReplyTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.other = UserFactory()
        self.ticket = SupportTicketFactory(
            user=self.owner,
            zendesk_ticket_id="987",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )
        self.outbox = SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            status=SupportTicketReplyOutbox.STATUS_FAILED,
            error_reason="Boom",
            attempt_count=3,
        )

    def _url(self):
        return reverse(
            "customercare.retry_outbox_reply",
            args=[self.ticket.id, self.outbox.id],
        )

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_owner_retry_resets_and_dispatches(self, mock_delay):
        self.client.force_login(self.owner)
        # Dispatch is via transaction.on_commit; force callbacks to fire under TestCase.
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self._url())
        self.assertEqual(302, response.status_code)
        self.outbox.refresh_from_db()
        self.assertEqual(self.outbox.status, SupportTicketReplyOutbox.STATUS_PENDING)
        self.assertEqual(self.outbox.error_reason, "")
        self.assertEqual(self.outbox.attempt_count, 0)
        mock_delay.assert_called_once_with(self.outbox.id)

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_second_retry_rejected_when_first_already_flipped_to_pending(self, mock_delay):
        """A second sequential retry finds the row already pending and aborts.

        Doesn't simulate true concurrency, but covers the post-transition gate
        that the SELECT FOR UPDATE lock makes safe under actual concurrency.
        """
        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            response1 = self.client.post(self._url())
            response2 = self.client.post(self._url())
        self.assertEqual(302, response1.status_code)
        self.assertEqual(400, response2.status_code)
        self.assertEqual(1, mock_delay.call_count)

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_htmx_retry_returns_partial(self, mock_delay):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id="thread-replies"')

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_retry_rejected_for_pending(self, mock_delay):
        self.outbox.status = SupportTicketReplyOutbox.STATUS_PENDING
        self.outbox.save()
        self.client.force_login(self.owner)
        response = self.client.post(self._url())
        self.assertEqual(400, response.status_code)
        mock_delay.assert_not_called()

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_retry_rejected_for_posted(self, mock_delay):
        self.outbox.status = SupportTicketReplyOutbox.STATUS_POSTED
        self.outbox.save()
        self.client.force_login(self.owner)
        response = self.client.post(self._url())
        self.assertEqual(400, response.status_code)
        mock_delay.assert_not_called()

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_retry_rejected_when_ticket_closed(self, mock_delay):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_CLOSED
        self.ticket.save()
        self.client.force_login(self.owner)
        response = self.client.post(self._url())
        self.assertEqual(400, response.status_code)
        mock_delay.assert_not_called()

    @patch("kitsune.customercare.views.post_outbox_reply.delay")
    def test_non_owner_retry_404(self, mock_delay):
        self.client.force_login(self.other)
        response = self.client.post(self._url())
        self.assertEqual(404, response.status_code)
        mock_delay.assert_not_called()

    def test_anonymous_retry_redirects(self):
        response = self.client.post(self._url())
        self.assertEqual(302, response.status_code)

    def test_get_method_not_allowed(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertEqual(405, response.status_code)


class TicketRepliesTemplateTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.ticket = SupportTicketFactory(
            user=self.owner,
            zendesk_ticket_id="987",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
            last_synced_at=timezone.now(),  # bypass needs_sync → includes the partial directly
        )

    def _url(self):
        return reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])

    def test_mirrored_and_outbox_both_render(self):
        self.ticket.comments = [
            {
                "id": 1,
                "body": "agent reply",
                "public": True,
                "author": {"id": 9, "name": "Agent"},
                "created_at": "2026-05-01T00:00:00Z",
            }
        ]
        self.ticket.save()
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket, author=self.owner, body="user pending reply"
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "agent reply")
        self.assertContains(response, "user pending reply")

    def test_posted_outbox_dropped_when_id_in_mirror(self):
        self.ticket.comments = [
            {
                "id": 42,
                "body": "mirrored body",
                "public": True,
                "author": {"id": 9, "name": "x"},
                "created_at": "2026-05-01T00:00:00Z",
            }
        ]
        self.ticket.save()
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            body="outbox body should not render",
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=42,
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "mirrored body")
        self.assertNotContains(response, "outbox body should not render")

    def test_private_mirrored_comments_not_rendered(self):
        self.ticket.comments = [
            {
                "id": 1,
                "body": "private agent note",
                "public": False,
                "author": {"id": 9, "name": "x"},
                "created_at": "2026-05-01T00:00:00Z",
            }
        ]
        self.ticket.save()
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "private agent note")

    def test_reply_form_shown_for_owner_active_ticket(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "question-reply-form")
        self.assertContains(response, "Post Reply")

    def test_reply_form_hidden_for_solved_ticket(self):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_SOLVED
        self.ticket.save()
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "Post Reply")
        self.assertContains(response, "This ticket is closed")

    def test_reply_form_hidden_for_staff_viewer(self):
        staff = UserFactory()
        perm = Permission.objects.get(codename="change_supportticket")
        staff.user_permissions.add(perm)
        self.client.force_login(staff)
        response = self.client.get(self._url())
        self.assertNotContains(response, "question-reply-form")

    def test_failed_outbox_shows_retry_button(self):
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            body="failed reply",
            status=SupportTicketReplyOutbox.STATUS_FAILED,
            error_reason="It broke",
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "Retry")
        self.assertContains(response, "It broke")

    def test_pending_outbox_shows_sending_indicator(self):
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            body="my pending reply",
            status=SupportTicketReplyOutbox.STATUS_PENDING,
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "my pending reply")
        self.assertContains(response, "thread-post--sending")

    def test_posted_outbox_does_not_show_sending_indicator(self):
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            body="my posted reply",
            status=SupportTicketReplyOutbox.STATUS_POSTED,
            zendesk_comment_id=42,
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "my posted reply")
        self.assertNotContains(response, "thread-post--sending")

    def test_polling_div_present_with_pending_outbox(self):
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            status=SupportTicketReplyOutbox.STATUS_PENDING,
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        # First poll: delay = poll_delays[0] = 2s.
        self.assertContains(response, 'hx-trigger="load delay:2s"')

    def test_polling_div_absent_with_no_pending(self):
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            status=SupportTicketReplyOutbox.STATUS_FAILED,
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "hx-trigger=\"load delay:")

    def test_polling_div_absent_at_max_poll_count(self):
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            status=SupportTicketReplyOutbox.STATUS_PENDING,
        )
        self.client.force_login(self.owner)
        # 8 backoff entries; poll_count=8 is past the cap so no polling div renders.
        response = self.client.get(self._url() + "?poll=8")
        self.assertNotContains(response, "hx-trigger=\"load delay:")

    def test_sending_indicator_hidden_once_polling_stops(self):
        """After the poll cap, a still-pending row should drop the misleading "Sending…"."""
        SupportTicketReplyOutboxFactory(
            ticket=self.ticket,
            author=self.owner,
            status=SupportTicketReplyOutbox.STATUS_PENDING,
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url() + "?poll=8")
        self.assertNotContains(response, "thread-post--sending")
