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

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tests import SupportTicketFactory
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
    """POST to ticket_detail creates/replaces/re-attempts the pending comment."""

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

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_owner_post_creates_pending_and_enqueues_task(self, mock_task):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "thanks!"})

        self.assertEqual(302, response.status_code)
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)
        pending = self.ticket.pending_changes["comment"]
        self.assertEqual("sending", pending["status"])
        self.assertEqual("thanks!", pending["body"])
        self.assertIsNone(pending["last_attempted_at"])
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_same_body_resubmit_reattempts_existing(self, mock_task):
        """Failed-retryable + same body → flip back to sending, keep attempts/last_attempted_at."""
        self.ticket.pending_changes["comment"] = {
            "body": "hello",
            "status": "failed",
            "allow_retries": True,
            "created_at": "2026-05-14T00:00:00Z",
            "last_attempted_at": "2026-05-14T00:00:05Z",
        }
        self.ticket.save(update_fields=["pending_changes"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "hello"})

        self.ticket.refresh_from_db()
        pending = self.ticket.pending_changes["comment"]
        self.assertEqual("sending", pending["status"])
        self.assertNotIn("allow_retries", pending)
        self.assertEqual("2026-05-14T00:00:05Z", pending["last_attempted_at"])
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_different_body_resubmit_replaces_pending(self, mock_task):
        """Failed + different body → replace pending with fresh attempts=0 entry."""
        self.ticket.pending_changes["comment"] = {
            "body": "old body",
            "status": "failed",
            "allow_retries": True,
            "created_at": "2026-05-14T00:00:00Z",
            "last_attempted_at": "2026-05-14T00:00:05Z",
        }
        self.ticket.save(update_fields=["pending_changes"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "new body"})

        self.ticket.refresh_from_db()
        pending = self.ticket.pending_changes["comment"]
        self.assertEqual("sending", pending["status"])
        self.assertEqual("new body", pending["body"])
        self.assertIsNone(pending["last_attempted_at"])
        self.assertNotIn("allow_retries", pending)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_same_body_when_allow_retries_false_still_retries(self, mock_task):
        """Failed + allow_retries=False + same body → retry anyway.

        The permanent classification is a hint, not a guarantee — the underlying
        issue may have been fixed by engineering. The user gets agency to try.
        """
        self.ticket.pending_changes["comment"] = {
            "body": "hello",
            "status": "failed",
            "allow_retries": False,
            "created_at": "2026-05-14T00:00:00Z",
            "last_attempted_at": "2026-05-14T00:00:05Z",
        }
        self.ticket.save(update_fields=["pending_changes"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "hello"}, HTTP_HX_REQUEST="true")

        self.ticket.refresh_from_db()
        pending = self.ticket.pending_changes["comment"]
        self.assertEqual("sending", pending["status"])
        self.assertNotIn("allow_retries", pending)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_different_body_when_allow_retries_false_is_allowed(self, mock_task):
        """Failed + allow_retries=False + different body → replace (user trying something new)."""
        self.ticket.pending_changes["comment"] = {
            "body": "bad body",
            "status": "failed",
            "allow_retries": False,
            "created_at": "2026-05-14T00:00:00Z",
            "last_attempted_at": "2026-05-14T00:00:05Z",
        }
        self.ticket.save(update_fields=["pending_changes"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "different body"})

        self.ticket.refresh_from_db()
        pending = self.ticket.pending_changes["comment"]
        self.assertEqual("sending", pending["status"])
        self.assertEqual("different body", pending["body"])
        mock_task.delay.assert_called_once()

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_post_during_sending_does_not_replace_pending(self, mock_task):
        """While the task is in flight, a new POST should not overwrite the pending."""
        self.ticket.pending_changes["comment"] = {
            "body": "sending body",
            "status": "sending",
            "created_at": timezone.now().isoformat(),
            "last_attempted_at": timezone.now().isoformat(),
        }
        self.ticket.save(update_fields=["pending_changes"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "different"}, HTTP_HX_REQUEST="true")

        self.ticket.refresh_from_db()
        pending = self.ticket.pending_changes["comment"]
        self.assertEqual("sending body", pending["body"])
        self.assertEqual("sending", pending["status"])
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_htmx_post_returns_partial_with_pending(self, mock_task):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "hi there"}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "hi there")
        self.assertContains(response, 'id="thread-replies"')
        mock_task.delay.assert_called_once()

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_non_owner_post_404(self, mock_task):
        """Non-owner without staff perm hits the owner-or-perm gate → 404."""
        self.client.force_login(self.other)
        response = self.client.post(self._url(), data={"body": "evil"})
        self.assertEqual(404, response.status_code)
        mock_task.delay.assert_not_called()
        self.ticket.refresh_from_db()
        self.assertEqual({}, self.ticket.pending_changes)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_staff_with_view_perm_cannot_post(self, mock_task):
        """Staff with change_supportticket can view but cannot post a reply."""
        staff = UserFactory()
        perm = Permission.objects.get(codename="change_supportticket")
        staff.user_permissions.add(perm)
        self.client.force_login(staff)
        response = self.client.post(self._url(), data={"body": "from staff"})

        self.assertEqual(404, response.status_code)
        mock_task.delay.assert_not_called()
        self.ticket.refresh_from_db()
        self.assertEqual({}, self.ticket.pending_changes)

    def test_anonymous_post_redirects(self):
        response = self.client.post(self._url(), data={"body": "hi"})
        self.assertEqual(302, response.status_code)
        self.assertIn("/users/login", response["Location"])

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_empty_body_renders_form_error(self, mock_task):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": ""}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Please enter a reply")
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_whitespace_only_body_renders_form_error(self, mock_task):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "   \n  "}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Please enter a reply")
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_oversized_body_renders_form_error(self, mock_task):
        self.client.force_login(self.owner)
        body = "x" * 65_536
        response = self.client.post(self._url(), data={"body": body}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "limited to")
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_post_strips_whitespace(self, mock_task):
        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "  hello!  "})
        self.ticket.refresh_from_db()
        self.assertEqual("hello!", self.ticket.pending_changes["comment"]["body"])


class TicketRepliesTemplateTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.ticket = SupportTicketFactory(
            user=self.owner,
            zendesk_ticket_id="987",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )
        self.ticket.last_synced_at = timezone.now()
        self.ticket.save()

    def _url(self):
        return reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])

    def test_reply_form_shown_for_owner_active_ticket(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "question-reply-form")
        self.assertContains(response, "Post Reply")

    def test_reply_form_shown_for_staff_viewer(self):
        staff = UserFactory()
        perm = Permission.objects.get(codename="change_supportticket")
        staff.user_permissions.add(perm)
        self.client.force_login(staff)
        response = self.client.get(self._url())
        self.assertContains(response, "question-reply-form")

    def test_thread_replies_wrapper_present(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, 'id="thread-replies"')

    def _set_pending(self, **overrides):
        entry = {
            "body": "hello",
            "status": "sending",
            "created_at": timezone.now().isoformat(),
            "last_attempted_at": None,
        }
        entry.update(overrides)
        self.ticket.pending_changes["comment"] = entry
        self.ticket.save(update_fields=["pending_changes"])

    def test_sending_entry_renders_in_thread_with_spinner(self):
        self._set_pending(last_attempted_at=timezone.now().isoformat(), attempts=1)
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "Sending")
        self.assertContains(response, "thread-post--sending")
        self.assertContains(response, 'id="pending-reply"')

    def test_sending_disables_reply_form(self):
        self._set_pending(last_attempted_at=timezone.now().isoformat(), attempts=1)
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "<fieldset disabled")

    def test_failed_retryable_renders_error_with_form_prefill(self):
        self._set_pending(
            status="failed",
            allow_retries=True,
            attempts=1,
            last_attempted_at=timezone.now().isoformat(),
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "Your reply failed to send")
        # Form pre-filled with the failed body.
        self.assertContains(response, "hello")
        # Form is NOT disabled.
        self.assertNotContains(response, "<fieldset disabled")
        # Pending isn't shown in the replies thread (failed state lives in the form).
        self.assertNotContains(response, 'id="pending-reply"')

    def test_failed_no_retries_renders_contact_support(self):
        self._set_pending(
            status="failed",
            allow_retries=False,
            attempts=1,
            last_attempted_at=timezone.now().isoformat(),
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "Your reply could not be sent")
        self.assertNotContains(response, 'id="pending-reply"')

    def test_polling_attrs_present_when_sending(self):
        self._set_pending(last_attempted_at=timezone.now().isoformat(), attempts=1)
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, 'hx-trigger="load delay:1s, every 2s"')

    def test_polling_attrs_absent_when_no_pending(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "every 2s")

    def test_polling_attrs_absent_when_failed(self):
        self._set_pending(
            status="failed",
            allow_retries=True,
            attempts=1,
            last_attempted_at=timezone.now().isoformat(),
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "every 2s")

    def test_stale_sending_renders_as_failed(self):
        """effective_pending coerces stale sending → failed-retryable."""
        from datetime import timedelta as _td

        self._set_pending(
            last_attempted_at=(timezone.now() - _td(seconds=120)).isoformat(),
            attempts=1,
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "Your reply failed to send")
        self.assertNotContains(response, 'id="pending-reply"')
        self.assertNotContains(response, "every 2s")
