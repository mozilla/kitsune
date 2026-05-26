import base64
import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from zenpy.lib.exception import APIException

from kitsune.customercare.models import SupportTicket, SupportTicketPendingChange
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.groups.models import GroupProfile
from kitsune.products.tests import ProductSupportConfigFactory, ZendeskConfigFactory
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

    @patch("kitsune.customercare.views.process_zendesk_update")
    def test_valid_request_returns_200(self, mock_task):
        response = self._post({"ticket_id": "123", "status": "open"})
        self.assertEqual(response.status_code, 200)
        mock_task.delay.assert_called_once()

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
        staff = UserFactory(is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )
        self.assertEqual(200, response.status_code)

    def test_subtree_member_can_view_org_ticket(self):
        """A teammate in the same org subtree can view tickets they didn't submit."""
        config = ProductSupportConfigFactory(
            product=self.ticket.product, zendesk_config=ZendeskConfigFactory(name="zd")
        )
        c1_group = Group.objects.create(name="company1")
        root_group = Group.objects.create(name="enterprise")
        root = GroupProfile.add_root(group=root_group, slug="enterprise")
        c1 = root.add_child(group=c1_group, slug="company1")
        config.hybrid_support_groups.add(c1_group)

        self.owner.groups.add(c1_group)
        self.ticket.org_group = c1
        self.ticket.save(update_fields=["org_group"])

        teammate = UserFactory()
        teammate.groups.add(c1_group)
        self.client.force_login(teammate)
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
        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)
        self.assertIsNotNone(pending)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        self.assertEqual("thanks!", pending.payload)
        self.assertIsNone(pending.last_attempted_at)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_same_body_resubmit_reattempts_existing(self, mock_task):
        """Failed + same body → flip in place, bump last_attempted_at."""
        prior_last_attempt = timezone.now() - timedelta(seconds=120)
        old = SupportTicketPendingChange.objects.create(
            ticket=self.ticket,
            kind=SupportTicketPendingChange.KIND_COMMENT,
            payload="hello",
            status=SupportTicketPendingChange.STATUS_FAILED,
            last_attempted_at=prior_last_attempt,
        )

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "hello"})

        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)
        self.assertIsNotNone(pending)
        self.assertEqual(old.id, pending.id)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        self.assertEqual("hello", pending.payload)
        self.assertGreater(pending.last_attempted_at, prior_last_attempt)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_different_body_resubmit_replaces_pending(self, mock_task):
        """Failed + different body → replace pending with fresh entry."""
        old = SupportTicketPendingChange.objects.create(
            ticket=self.ticket,
            kind=SupportTicketPendingChange.KIND_COMMENT,
            payload="old body",
            status=SupportTicketPendingChange.STATUS_FAILED,
            last_attempted_at=timezone.now() - timedelta(seconds=120),
        )

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "new body"})

        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)
        self.assertIsNotNone(pending)
        self.assertNotEqual(old.id, pending.id)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        self.assertEqual("new body", pending.payload)
        self.assertIsNone(pending.last_attempted_at)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_post_during_sending_does_not_replace_pending(self, mock_task):
        """While the task is in flight, a new POST should not overwrite the pending."""
        existing = SupportTicketPendingChange.objects.create(
            ticket=self.ticket,
            kind=SupportTicketPendingChange.KIND_COMMENT,
            payload="sending body",
            status=SupportTicketPendingChange.STATUS_SENDING,
            last_attempted_at=timezone.now(),
        )

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"body": "different"}, HTTP_HX_REQUEST="true")

        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)
        self.assertEqual(existing.id, pending.id)
        self.assertEqual("sending body", pending.payload)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_create_race_integrity_error_is_silent_noop(self, mock_task):
        """Race between two first-time POSTs: the loser hits the (ticket, kind)
        unique constraint on create. The view should swallow the IntegrityError,
        skip the task enqueue, and render normally (no 500)."""
        self.client.force_login(self.owner)
        with patch.object(
            SupportTicketPendingChange.objects,
            "create",
            side_effect=IntegrityError("duplicate key value violates unique constraint"),
        ):
            response = self.client.post(self._url(), data={"body": "hello"})

        self.assertEqual(200, response.status_code)
        mock_task.delay.assert_not_called()
        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT))

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_create_race_returns_winner_without_dispatching(self, mock_task):
        """When the create race has a real winner: the loser's INSERT fails on
        the unique constraint, the view falls back to fetching the existing
        row, and renders with the winner's pending instead of None.

        Simulates real race timing by pre-creating the winner row and stubbing
        pending_change for the three calls the view makes on the losing path:
          1. initial unlocked read (winner hadn't committed yet → None)
          2. locked refetch (still in the race window → None)
          3. fallback after IntegrityError on create (winner now visible)
        The DB's unique constraint raises the IntegrityError naturally.
        """
        self.client.force_login(self.owner)

        winner = SupportTicketPendingChange.objects.create(
            ticket=self.ticket,
            kind=SupportTicketPendingChange.KIND_COMMENT,
            payload="winner body",
        )

        with patch.object(SupportTicket, "pending_change", side_effect=[None, None, winner]):
            response = self.client.post(self._url(), data={"body": "loser body"})

        self.assertEqual(200, response.status_code)
        mock_task.delay.assert_not_called()
        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)
        self.assertIsNotNone(pending)
        self.assertEqual("winner body", pending.payload)

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
        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT))

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_staff_with_view_perm_cannot_post(self, mock_task):
        """Staff with change_supportticket cannot view or post a reply."""
        staff = UserFactory()
        perm = Permission.objects.get(codename="change_supportticket")
        staff.user_permissions.add(perm)
        self.client.force_login(staff)
        response = self.client.post(self._url(), data={"body": "from staff"})

        self.assertEqual(404, response.status_code)
        mock_task.delay.assert_not_called()
        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT))

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
        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)
        self.assertEqual("hello!", pending.payload)

    @patch("kitsune.customercare.views.post_reply_to_zendesk")
    def test_post_on_closed_ticket_is_noop(self, mock_task):
        """Zendesk rejects comments on closed tickets, so the view drops the POST."""
        self.ticket.zd_status = SupportTicket.ZD_STATUS_CLOSED
        self.ticket.save(update_fields=["zd_status"])

        self.client.force_login(self.owner)
        response = self.client.post(self._url(), data={"body": "stale"})

        self.assertEqual(200, response.status_code)
        mock_task.delay.assert_not_called()
        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT))


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

    def test_thread_replies_wrapper_present(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, 'id="thread-replies"')

    def _set_pending(self, **overrides):
        self.ticket.pending_changes.filter(kind=SupportTicketPendingChange.KIND_COMMENT).delete()
        kwargs = {
            "ticket": self.ticket,
            "kind": SupportTicketPendingChange.KIND_COMMENT,
            "payload": "hello",
            "status": SupportTicketPendingChange.STATUS_SENDING,
            "last_attempted_at": None,
        }
        kwargs.update(overrides)
        return SupportTicketPendingChange.objects.create(**kwargs)

    def test_sending_entry_renders_in_thread_with_spinner(self):
        self._set_pending(last_attempted_at=timezone.now())
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "Sending")
        self.assertContains(response, "thread-post--sending")
        self.assertContains(response, 'id="pending-reply"')

    def test_sending_disables_reply_form(self):
        self._set_pending(last_attempted_at=timezone.now())
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "<fieldset disabled")

    def test_failed_renders_error_with_form_prefill(self):
        self._set_pending(
            status=SupportTicketPendingChange.STATUS_FAILED,
            last_attempted_at=timezone.now(),
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

    def test_polling_attrs_present_when_sending(self):
        self._set_pending(last_attempted_at=timezone.now())
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, 'hx-trigger="load delay:1s, every 2s"')

    def test_polling_attrs_absent_when_no_pending(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "every 2s")

    def test_polling_attrs_absent_when_failed(self):
        self._set_pending(
            status=SupportTicketPendingChange.STATUS_FAILED,
            last_attempted_at=timezone.now(),
        )
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "every 2s")

    def test_stale_sending_renders_as_failed(self):
        """effective_status coerces stale sending → failed."""
        self._set_pending(last_attempted_at=timezone.now() - timedelta(seconds=120))
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertContains(response, "Your reply failed to send")
        self.assertNotContains(response, 'id="pending-reply"')
        self.assertNotContains(response, "every 2s")

    def test_closed_ticket_hides_reply_form_and_shows_notice(self):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_CLOSED
        self.ticket.save(update_fields=["zd_status"])
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertNotContains(response, "question-reply-form")
        self.assertNotContains(response, "Post Reply")
        self.assertContains(response, "can no longer receive replies")


class TicketStatusViewTests(TestCase):
    """POST/GET to ticket_status: creates/retries the pending zd_status
    change and dispatches the worker task. Access-control mirrors ticket_detail.
    """

    def setUp(self):
        self.owner = UserFactory()
        self.other = UserFactory()
        self.ticket = SupportTicketFactory(
            user=self.owner,
            zendesk_ticket_id="987",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
        )

    def _url(self):
        return reverse("customercare.ticket_status", args=[self.owner.username, self.ticket.id])

    def _detail_url(self):
        return reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_owner_post_creates_pending_and_enqueues_task(self, mock_task):
        self.client.force_login(self.owner)
        response = self.client.post(
            self._url(), data={"target_status": SupportTicket.ZD_STATUS_SOLVED}
        )

        self.assertEqual(302, response.status_code)
        self.ticket.refresh_from_db()
        self.assertEqual(SupportTicket.ZD_STATUS_OPEN, self.ticket.zd_status)
        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS)
        self.assertIsNotNone(pending)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        self.assertEqual(SupportTicket.ZD_STATUS_SOLVED, pending.payload)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_retry_after_failure_reattempts_existing_pending(self, mock_task):
        """Failed pending + same/valid target → flip in place, bump timestamp."""
        prior_last_attempt = timezone.now() - timedelta(seconds=120)
        prior = SupportTicketPendingChange.objects.create(
            ticket=self.ticket,
            kind=SupportTicketPendingChange.KIND_ZD_STATUS,
            payload=SupportTicket.ZD_STATUS_SOLVED,
            status=SupportTicketPendingChange.STATUS_FAILED,
            last_attempted_at=prior_last_attempt,
        )

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"target_status": SupportTicket.ZD_STATUS_SOLVED})

        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS)
        self.assertEqual(prior.id, pending.id)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        self.assertEqual(SupportTicket.ZD_STATUS_SOLVED, pending.payload)
        self.assertGreater(pending.last_attempted_at, prior_last_attempt)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_post_during_sending_does_not_replace_pending(self, mock_task):
        """While the task is in flight, a new POST should not overwrite the pending."""
        existing = SupportTicketPendingChange.objects.create(
            ticket=self.ticket,
            kind=SupportTicketPendingChange.KIND_ZD_STATUS,
            payload=SupportTicket.ZD_STATUS_SOLVED,
            status=SupportTicketPendingChange.STATUS_SENDING,
            last_attempted_at=timezone.now(),
        )

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"target_status": SupportTicket.ZD_STATUS_SOLVED})

        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS)
        self.assertEqual(existing.id, pending.id)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_invalid_target_status_is_noop(self, mock_task):
        """Target status not in permitted set → no pending, no task."""
        self.client.force_login(self.owner)
        response = self.client.post(
            self._url(), data={"target_status": SupportTicket.ZD_STATUS_CLOSED}
        )

        self.assertEqual(302, response.status_code)
        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS))
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_missing_target_status_is_noop(self, mock_task):
        self.client.force_login(self.owner)
        self.client.post(self._url(), data={})

        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS))
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_target_blocked_by_zd_status(self, mock_task):
        """Closed tickets cannot be reopened by the owner."""
        self.ticket.zd_status = SupportTicket.ZD_STATUS_CLOSED
        self.ticket.save(update_fields=["zd_status"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"target_status": SupportTicket.ZD_STATUS_OPEN})

        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS))
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_target_blocked_by_submission_status(self, mock_task):
        """Tickets that have not been sent to Zendesk cannot be transitioned."""
        self.ticket.submission_status = SupportTicket.STATUS_PENDING
        self.ticket.save(update_fields=["submission_status"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"target_status": SupportTicket.ZD_STATUS_SOLVED})

        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS))
        mock_task.delay.assert_not_called()

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_solved_ticket_can_be_reopened(self, mock_task):
        """Owner-driven reopen flow: SOLVED → OPEN is the only permitted transition."""
        self.ticket.zd_status = SupportTicket.ZD_STATUS_SOLVED
        self.ticket.save(update_fields=["zd_status"])

        self.client.force_login(self.owner)
        self.client.post(self._url(), data={"target_status": SupportTicket.ZD_STATUS_OPEN})

        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS)
        self.assertIsNotNone(pending)
        self.assertEqual(SupportTicket.ZD_STATUS_OPEN, pending.payload)
        self.assertEqual(SupportTicketPendingChange.STATUS_SENDING, pending.status)
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_create_race_integrity_error_is_silent_noop(self, mock_task):
        """Race between two first-time POSTs: the loser hits the (ticket, kind)
        unique constraint on create. The view should swallow the IntegrityError,
        skip the task enqueue, and render normally (no 500)."""
        self.client.force_login(self.owner)
        with patch.object(
            SupportTicketPendingChange.objects,
            "create",
            side_effect=IntegrityError("duplicate key"),
        ):
            response = self.client.post(
                self._url(), data={"target_status": SupportTicket.ZD_STATUS_SOLVED}
            )

        self.assertEqual(302, response.status_code)
        mock_task.delay.assert_not_called()
        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS))

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_htmx_post_returns_partial(self, mock_task):
        self.client.force_login(self.owner)
        response = self.client.post(
            self._url(),
            data={"target_status": SupportTicket.ZD_STATUS_SOLVED},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id="thread-status"')
        mock_task.delay.assert_called_once_with(ticket_id=self.ticket.id)

    def test_htmx_get_returns_partial(self):
        """HTMX poll during sending refreshes the cluster without doing anything else."""
        self.client.force_login(self.owner)
        response = self.client.get(self._url(), HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id="thread-status"')

    def test_non_htmx_get_redirects_to_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(self._url())
        self.assertEqual(302, response.status_code)
        self.assertIn(self._detail_url(), response["Location"])

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_non_owner_post_404(self, mock_task):
        self.client.force_login(self.other)
        response = self.client.post(
            self._url(), data={"target_status": SupportTicket.ZD_STATUS_SOLVED}
        )
        self.assertEqual(404, response.status_code)
        mock_task.delay.assert_not_called()
        self.assertIsNone(self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS))

    def test_non_owner_get_404(self):
        self.client.force_login(self.other)
        response = self.client.get(self._url())
        self.assertEqual(404, response.status_code)

    def test_anonymous_post_redirects_to_login(self):
        response = self.client.post(
            self._url(), data={"target_status": SupportTicket.ZD_STATUS_SOLVED}
        )
        self.assertEqual(302, response.status_code)
        self.assertIn("/users/login", response["Location"])

    @patch("kitsune.customercare.views.post_status_change_to_zendesk")
    def test_get_method_does_not_dispatch_task(self, mock_task):
        """Defense-in-depth: only POST creates pending and dispatches."""
        SupportTicketPendingChange.objects.create(
            ticket=self.ticket,
            kind=SupportTicketPendingChange.KIND_ZD_STATUS,
            payload=SupportTicket.ZD_STATUS_SOLVED,
            status=SupportTicketPendingChange.STATUS_FAILED,
            last_attempted_at=timezone.now() - timedelta(seconds=120),
        )

        self.client.force_login(self.owner)
        self.client.get(self._url(), HTTP_HX_REQUEST="true")

        pending = self.ticket.pending_change(SupportTicketPendingChange.KIND_ZD_STATUS)
        self.assertEqual(SupportTicketPendingChange.STATUS_FAILED, pending.status)
        mock_task.delay.assert_not_called()
