import base64
import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse
from zenpy.lib.exception import APIException

from kitsune.customercare.forms import SupportTicketReplyForm
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


def _build_audit(comment_id, body="reply body", updated_at="2026-05-12T00:00:00Z"):
    """TicketAudit-shaped: .audit.events is a list of comment dicts; .ticket carries updated_at."""
    audit = SimpleNamespace(
        events=[
            {
                "id": comment_id,
                "type": "Comment",
                "author_id": 999,
                "body": body,
                "public": True,
            }
        ]
    )
    ticket = SimpleNamespace(updated_at=updated_at)
    return SimpleNamespace(audit=audit, ticket=ticket)


class TicketReplyPostTests(TestCase):
    """POST to ticket_detail posts a reply synchronously to Zendesk."""

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

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_owner_post_calls_zendesk_and_appends_mirror(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = _build_audit(
            42, body="thanks!"
        )
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "thanks!"})

        self.assertEqual(302, response.status_code)
        mock_client_cls.assert_called_once_with(timeout=10)
        mock_client_cls.return_value.add_ticket_comment.assert_called_once_with(
            user=self.owner,
            ticket_id="987",
            comment_body="thanks!",
            public=True,
        )
        self.ticket.refresh_from_db()
        self.assertEqual(1, len(self.ticket.comments))
        stored = self.ticket.comments[0]
        self.assertEqual(42, stored["id"])
        self.assertEqual("thanks!", stored["body"])
        self.assertTrue(stored["public"])
        self.assertEqual(self.owner.profile.display_name, stored["author"]["name"])

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_htmx_post_returns_partial_with_new_comment(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = _build_audit(
            42, body="hi there"
        )
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "hi there"}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "hi there")
        self.assertContains(response, 'id="thread-replies"')

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_non_owner_post_404(self, mock_client_cls):
        """Non-owner without staff perm hits the owner-or-perm gate → 404."""
        self.client.force_login(self.other)
        response = self.client.post(self._url(), data={"body": "evil"})
        self.assertEqual(404, response.status_code)
        mock_client_cls.assert_not_called()
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_staff_with_perm_can_post(self, mock_client_cls):
        """A staff member with change_supportticket can reply on the owner's ticket."""
        mock_client_cls.return_value.add_ticket_comment.return_value = _build_audit(
            7, body="from staff"
        )
        staff = UserFactory()
        perm = Permission.objects.get(codename="change_supportticket")
        staff.user_permissions.add(perm)
        self.client.force_login(staff)
        response = self.client.post(self._url(), data={"body": "from staff"})

        self.assertEqual(302, response.status_code)
        mock_client_cls.return_value.add_ticket_comment.assert_called_once_with(
            user=staff,
            ticket_id="987",
            comment_body="from staff",
            public=True,
        )
        self.ticket.refresh_from_db()
        self.assertEqual(1, len(self.ticket.comments))
        self.assertEqual(staff.profile.display_name, self.ticket.comments[0]["author"]["name"])

    def test_anonymous_post_redirects(self):
        response = self.client.post(self._url(), data={"body": "hi"})
        self.assertEqual(302, response.status_code)
        self.assertIn("/users/login", response["Location"])

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_renders_closed_notice_when_solved(self, mock_client_cls):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_SOLVED
        self.ticket.save()
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "hi"})
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "This ticket is closed")
        mock_client_cls.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_renders_closed_notice_when_closed(self, mock_client_cls):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_CLOSED
        self.ticket.save()
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "hi"})
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "This ticket is closed")
        mock_client_cls.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_empty_body_renders_form_error(self, mock_client_cls):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": ""}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Please enter a reply")
        mock_client_cls.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_whitespace_only_body_renders_form_error(self, mock_client_cls):
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "   \n  "}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Please enter a reply")
        mock_client_cls.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_oversized_body_renders_form_error(self, mock_client_cls):
        self.client.force_login(self.owner)
        body = "x" * (SupportTicketReplyForm.BODY_MAX_LENGTH + 1)
        response = self.client.post(self._url(), data={"body": body}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "limited to")
        mock_client_cls.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_strips_whitespace(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = _build_audit(7)
        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "  hello!  "})
        called_with = mock_client_cls.return_value.add_ticket_comment.call_args.kwargs
        self.assertEqual("hello!", called_with["comment_body"])

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_retriable_zendesk_5xx_renders_try_again(self, mock_client_cls):
        response_mock = MagicMock(status_code=503)
        mock_client_cls.return_value.add_ticket_comment.side_effect = APIException(
            "zendesk", response=response_mock
        )
        self.client.force_login(self.owner)
        response = self.client.post(
            self._url(), data={"body": "transient"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Something went wrong")
        self.assertContains(response, "try again")
        # body preserved for editing
        self.assertContains(response, "transient")
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_retriable_connection_error_renders_try_again(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.side_effect = (
            requests.exceptions.ConnectionError("boom")
        )
        self.client.force_login(self.owner)
        response = self.client.post(
            self._url(), data={"body": "network sad"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Something went wrong")
        self.assertContains(response, "network sad")
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_permanent_zendesk_4xx_renders_contact_support(self, mock_client_cls):
        response_mock = MagicMock(status_code=422)
        mock_client_cls.return_value.add_ticket_comment.side_effect = APIException(
            "zendesk", response=response_mock
        )
        self.client.force_login(self.owner)
        response = self.client.post(
            self._url(), data={"body": "validation fail"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "contact support")
        self.assertNotContains(response, "try again")
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_audit_with_no_comment_event_succeeds_without_appending(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = SimpleNamespace(
            audit=SimpleNamespace(events=[]),
            ticket=SimpleNamespace(updated_at="2026-05-12T00:00:00Z"),
        )
        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "ok"})
        self.assertEqual(302, response.status_code)
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_mirror_append_dedupes_when_id_already_present(self, mock_client_cls):
        """If the webhook landed first, the view append should not duplicate."""
        self.ticket.comments = [
            {"id": 42, "body": "already mirrored", "public": True, "author": {}}
        ]
        self.ticket.save()
        mock_client_cls.return_value.add_ticket_comment.return_value = _build_audit(42)
        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "double-post attempt"})
        self.ticket.refresh_from_db()
        self.assertEqual(1, len(self.ticket.comments))


class TicketRepliesTemplateTests(TestCase):
    def setUp(self):
        self.owner = UserFactory()
        self.ticket = SupportTicketFactory(
            user=self.owner,
            zendesk_ticket_id="987",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )
        from django.utils import timezone

        self.ticket.last_synced_at = timezone.now()
        self.ticket.save()

    def _url(self):
        return reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])

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
        self.assertNotContains(response, "question-reply-form")
        self.assertContains(response, "This ticket is closed")

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
