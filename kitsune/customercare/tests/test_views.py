import base64
import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import Group
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from pyquery import PyQuery as pq
from zenpy.lib.exception import APIException, RecordNotFoundException

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.groups.models import GroupProfile
from kitsune.products.tests import ProductSupportConfigFactory, ZendeskConfigFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse as reverse_locale
from kitsune.users.tests import UserFactory

WEBHOOK_API_KEY = "test-webhook-api-key"
WEBHOOK_SIGNING_SECRET = "test-webhook-secret"
WEBHOOK_URL = "/customercare/zendesk/updates"


def _sign_payload(body, timestamp="1234567890", secret=WEBHOOK_SIGNING_SECRET):
    """Generate a valid HMAC-SHA256 signature for the given payload."""
    message = timestamp.encode("utf-8") + body
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def _make_viewable_by_teammate(owner, ticket):
    """Wire up a hybrid org so a teammate in the same company subtree can VIEW
    `ticket`. Per issue #3069 such a teammate still must not be able to reply."""
    config = ProductSupportConfigFactory(
        product=ticket.product, zendesk_config=ZendeskConfigFactory(name="zd")
    )
    company_group = Group.objects.create(name="company1")
    root = GroupProfile.add_root(group=Group.objects.create(name="enterprise"), slug="enterprise")
    company = root.add_child(group=company_group, slug="company1")
    config.hybrid_support_groups.add(company_group)
    owner.groups.add(company_group)
    ticket.org_group = company
    ticket.save(update_fields=["org_group"])
    teammate = UserFactory()
    teammate.groups.add(company_group)
    return teammate


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

    def test_non_owner_viewer_sees_note_not_form(self):
        """A teammate viewing someone else's ticket gets a read-only note, no form."""
        teammate = _make_viewable_by_teammate(self.owner, self.ticket)
        self.client.force_login(teammate)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )

        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "question-reply-form")
        self.assertNotContains(response, "Post Reply")
        self.assertContains(response, "Only the ticket creator can reply")

    def test_deleted_ticket_shows_readonly_banner_and_hides_form(self):
        """A ticket deleted in Zendesk shows the read-only notice, not the reply form."""
        self.ticket.update(zd_deleted_at=timezone.now())
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id])
        )

        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "question-reply-form")
        self.assertNotContains(response, "Post Reply")
        self.assertContains(response, "This ticket can no longer receive replies")
        # Hero status pill reads "Inactive" rather than the stale zd_status.
        self.assertContains(response, "Inactive")

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
        mock_sync.return_value = self.ticket
        self.client.force_login(self.owner)
        response = self._htmx_get()
        self.assertEqual(200, response.status_code)
        mock_sync.assert_called_once_with(self.ticket)

    @patch(
        "kitsune.customercare.utils.fetch_zendesk_ticket_data",
        side_effect=RecordNotFoundException,
    )
    def test_htmx_sync_self_heals_when_ticket_deleted(self, mock_fetch):
        """If Zendesk 404s during the on-view sync, the view must re-render from the
        self-healed ticket: banner + Inactive pill, not a stale status + reply form."""
        self.client.force_login(self.owner)
        response = self._htmx_get()

        self.assertEqual(200, response.status_code)
        self.ticket.refresh_from_db()
        self.assertIsNotNone(self.ticket.zd_deleted_at)
        self.assertContains(response, "This ticket can no longer receive replies")
        self.assertContains(response, "Inactive")
        self.assertNotContains(response, "Post Reply")

    @patch("kitsune.customercare.views.sync_ticket_from_zendesk")
    def test_zd_failure_returns_error_partial(self, mock_sync):
        mock_sync.side_effect = APIException("ZD unreachable")
        self.client.force_login(self.owner)
        response = self._htmx_get()
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "latest replies")

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_htmx_sync_status_change_oob_swaps_pill(self, mock_client_cls):
        """A GET sync that changes zd_status re-renders from the synced ticket and
        OOB-swaps the hero pill cluster to the new status."""
        self.ticket.zd_status = SupportTicket.ZD_STATUS_OPEN
        self.ticket.save(update_fields=["zd_status"])
        mock_client = mock_client_cls.return_value
        mock_client.get_ticket_comments.return_value = []
        mock_client.get_ticket.return_value = MagicMock(
            status="solved",
            updated_at=timezone.now(),
            subject=self.ticket.subject,
            description=self.ticket.description,
        )

        self.client.force_login(self.owner)
        response = self._htmx_get()

        self.assertEqual(200, response.status_code)
        self.ticket.refresh_from_db()
        self.assertEqual(SupportTicket.ZD_STATUS_SOLVED, self.ticket.zd_status)
        self.assertContains(response, 'id="thread-detail--pill-cluster"')
        self.assertContains(response, 'hx-swap-oob="true"')
        self.assertContains(response, "status-label--solved")

    @patch("kitsune.customercare.utils.ZendeskClient")
    def test_htmx_sync_without_status_change_omits_oob_badge(self, mock_client_cls):
        """A GET sync that leaves zd_status unchanged emits no OOB pill swap."""
        self.ticket.zd_status = SupportTicket.ZD_STATUS_OPEN
        self.ticket.save(update_fields=["zd_status"])
        mock_client = mock_client_cls.return_value
        mock_client.get_ticket_comments.return_value = []
        mock_client.get_ticket.return_value = MagicMock(
            status="open",
            updated_at=timezone.now(),
            subject=self.ticket.subject,
            description=self.ticket.description,
        )

        self.client.force_login(self.owner)
        response = self._htmx_get()

        self.assertEqual(200, response.status_code)
        self.assertNotIn(b'hx-swap-oob="true"', response.content)
        self.assertNotIn(b'id="thread-detail--pill-cluster"', response.content)

    def test_non_owner_htmx_gets_404(self):
        self.client.force_login(self.other)
        response = self._htmx_get()
        self.assertEqual(404, response.status_code)

    def test_anonymous_htmx_redirects(self):
        response = self._htmx_get()
        self.assertEqual(302, response.status_code)


class TicketReplySyncTests(TestCase):
    """Tests for the synchronous reply flow in ticket_detail."""

    def setUp(self):
        self.owner = UserFactory()
        self.owner.profile.zendesk_id = "999"
        self.owner.profile.save(update_fields=["zendesk_id"])
        self.ticket = SupportTicketFactory(
            user=self.owner,
            zendesk_ticket_id="42",
            zd_status=SupportTicket.ZD_STATUS_OPEN,
            comments=[],
        )
        self.client.force_login(self.owner)
        self.url = reverse(
            "customercare.ticket_detail", args=[self.owner.username, self.ticket.id]
        )

    def _audit(self, status="open", updated_at="2026-05-28T12:00:00Z", comment_id=1234):
        """Return a stand-in for ZendeskClient.add_ticket_comment's return value."""
        ticket_view = SimpleNamespace(
            id=int(self.ticket.zendesk_ticket_id),
            status=status,
            updated_at=updated_at,
        )
        events = [
            {
                "type": "Comment",
                "id": comment_id,
                "html_body": "<p>hello</p>",
                "author_id": 999,
            }
        ]
        audit = SimpleNamespace(events=events)
        return SimpleNamespace(ticket=ticket_view, audit=audit)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_calls_zendesk_with_expected_args(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit()
        self.client.post(self.url, {"body": "hello"})
        mock_client_cls.assert_called_with()
        mock_client_cls.return_value.add_ticket_comment.assert_called_once()
        kwargs = mock_client_cls.return_value.add_ticket_comment.call_args.kwargs
        self.assertEqual(self.owner, kwargs["user"])
        self.assertEqual(42, kwargs["ticket_id"])
        self.assertEqual("hello", kwargs["comment_body"])
        self.assertTrue(kwargs["public"])
        self.assertIsNone(kwargs["status"])

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_reply_blocked_for_deleted_ticket(self, mock_client_cls):
        self.ticket.update(zd_deleted_at=timezone.now())

        self.client.post(self.url, {"body": "hello"})

        mock_client_cls.return_value.add_ticket_comment.assert_not_called()
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_reply_self_heals_when_ticket_deleted_mid_request(self, mock_client_cls):
        """If the ticket is deleted in Zendesk between load and reply, self-heal to
        read-only and show the banner instead of a 'failed to send' error."""
        mock_client_cls.return_value.add_ticket_comment.side_effect = RecordNotFoundException

        response = self.client.post(self.url, {"body": "hello"}, HTTP_HX_REQUEST="true")

        self.ticket.refresh_from_db()
        self.assertIsNotNone(self.ticket.zd_deleted_at)
        self.assertEqual([], self.ticket.comments)
        self.assertContains(response, "This ticket can no longer receive replies")
        self.assertNotContains(response, "failed to send")

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_pending_ticket_reopens_on_reply(self, mock_client_cls):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_PENDING
        self.ticket.save(update_fields=["zd_status"])
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit(status="open")
        self.client.post(self.url, {"body": "hi"})
        kwargs = mock_client_cls.return_value.add_ticket_comment.call_args.kwargs
        self.assertEqual(SupportTicket.ZD_STATUS_OPEN, kwargs["status"])

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_persists_status_updated_at_and_appends_comment(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit(
            status="pending",
            updated_at="2026-05-28T12:34:56Z",
            comment_id=5678,
        )
        self.client.post(self.url, {"body": "hi"})
        self.ticket.refresh_from_db()
        self.assertEqual("pending", self.ticket.zd_status)
        self.assertEqual(parse_datetime("2026-05-28T12:34:56Z"), self.ticket.zd_updated_at)
        self.assertEqual(1, len(self.ticket.comments))
        self.assertEqual(5678, self.ticket.comments[0]["id"])
        self.assertEqual("<p>hello</p>", self.ticket.comments[0]["body"])
        self.assertEqual(
            self.owner.profile.display_name,
            self.ticket.comments[0]["author"]["name"],
        )

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_redirects_on_non_htmx_success(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit()
        response = self.client.post(self.url, {"body": "hi"})
        self.assertRedirects(response, self.url)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_htmx_post_renders_partial_with_fresh_form(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit()
        response = self.client.post(self.url, {"body": "hi"}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        # Partial template renders the thread-replies wrapper
        self.assertContains(response, 'id="thread-replies"')
        # New unbound form — textarea is empty in rendered HTML
        self.assertNotIn(b"hi</textarea>", response.content)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_zendesk_api_exception_sets_reply_error(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.side_effect = APIException("nope")
        response = self.client.post(self.url, {"body": "kept on failure"}, HTTP_HX_REQUEST="true")
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)
        self.assertEqual(SupportTicket.ZD_STATUS_OPEN, self.ticket.zd_status)
        # Bound form preserves the user's body
        self.assertIn(b"kept on failure", response.content)
        self.assertIn(b"failed to send", response.content.lower())

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_request_exception_sets_reply_error(self, mock_client_cls):
        mock_client_cls.return_value.add_ticket_comment.side_effect = (
            requests.exceptions.RequestException("network")
        )
        response = self.client.post(self.url, {"body": "x"}, HTTP_HX_REQUEST="true")
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)
        self.assertIn(b"failed to send", response.content.lower())

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_audit_without_comment_event_sets_reply_error(self, mock_client_cls):
        audit = self._audit()
        audit.audit.events = []  # No Comment event
        mock_client_cls.return_value.add_ticket_comment.return_value = audit
        response = self.client.post(self.url, {"body": "x"}, HTTP_HX_REQUEST="true")
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)
        self.assertIn(b"failed to send", response.content.lower())

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_on_closed_ticket_skips_zendesk(self, mock_client_cls):
        self.ticket.zd_status = SupportTicket.ZD_STATUS_CLOSED
        self.ticket.save(update_fields=["zd_status"])
        self.client.post(self.url, {"body": "ignored"})
        mock_client_cls.return_value.add_ticket_comment.assert_not_called()
        self.ticket.refresh_from_db()
        self.assertEqual([], self.ticket.comments)

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_dedupes_existing_comment_id(self, mock_client_cls):
        self.ticket.comments = [
            {
                "id": 5678,
                "body": "<p>already here</p>",
                "created_at": "2026-05-28T12:00:00Z",
                "public": True,
                "author": {"name": "Owner", "id": 999},
            }
        ]
        self.ticket.save(update_fields=["comments"])
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit(
            status="pending",
            updated_at="2026-05-28T13:00:00Z",
            comment_id=5678,
        )
        self.client.post(self.url, {"body": "x"})
        self.ticket.refresh_from_db()
        self.assertEqual(1, len(self.ticket.comments))  # Not duplicated
        self.assertEqual("pending", self.ticket.zd_status)  # But status still updated

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_post_by_non_owner_returns_404(self, mock_client_cls):
        other = UserFactory()
        self.client.force_login(other)
        response = self.client.post(self.url, {"body": "trespasser"})
        self.assertEqual(404, response.status_code)
        mock_client_cls.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_subtree_teammate_cannot_post(self, mock_client_cls):
        """A teammate who CAN view the ticket (same org subtree) still cannot reply;
        only the owner can. Regression for issue #3069."""
        teammate = _make_viewable_by_teammate(self.owner, self.ticket)
        self.client.force_login(teammate)
        response = self.client.post(self.url, {"body": "not mine"})

        self.assertEqual(403, response.status_code)
        mock_client_cls.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_empty_body_renders_form_error(self, mock_client_cls):
        response = self.client.post(self.url, {"body": ""}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Please enter a reply")
        mock_client_cls.return_value.add_ticket_comment.assert_not_called()

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_htmx_post_includes_oob_status_badge(self, mock_client_cls):
        """HTMX response carries an OOB pill cluster reflecting the new status."""
        self.ticket.zd_status = SupportTicket.ZD_STATUS_PENDING
        self.ticket.save(update_fields=["zd_status"])
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit(status="open")
        response = self.client.post(self.url, {"body": "hi"}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id="thread-detail--pill-cluster"')
        self.assertContains(response, 'hx-swap-oob="true"')

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_htmx_post_without_status_change_omits_oob_badge(self, mock_client_cls):
        """No status change means no OOB swap (the hero pill is already correct)."""
        # Ticket starts open; audit reports open — no status change.
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit(status="open")
        response = self.client.post(self.url, {"body": "hi"}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertNotIn(b'hx-swap-oob="true"', response.content)
        self.assertNotIn(b'id="thread-detail--pill-cluster"', response.content)

    def test_non_htmx_render_emits_single_pill_cluster(self):
        """Initial page render must NOT duplicate the pill cluster element."""
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        # Exactly one `id="thread-detail--pill-cluster"` should appear:
        # the one in the hero. The OOB block must be gated off.
        self.assertEqual(1, response.content.count(b'id="thread-detail--pill-cluster"'))

    @patch("kitsune.customercare.views.ZendeskClient")
    def test_htmx_post_removes_pending_notice_via_oob(self, mock_client_cls):
        """Reopening a PENDING ticket OOB-swaps an empty notice slot, clearing
        the 'waiting for your response' banner without a full reload (#3078)."""
        self.ticket.zd_status = SupportTicket.ZD_STATUS_PENDING
        self.ticket.save(update_fields=["zd_status"])
        mock_client_cls.return_value.add_ticket_comment.return_value = self._audit(status="open")
        response = self.client.post(self.url, {"body": "hi"}, HTTP_HX_REQUEST="true")
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id="thread-detail--notice-slot"')
        self.assertContains(response, 'hx-swap-oob="true"')
        self.assertNotIn(b"waiting for your response", response.content)

    def test_non_htmx_render_emits_single_notice_slot(self):
        """Initial page render must NOT duplicate the notice slot element."""
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.content.count(b'id="thread-detail--notice-slot"'))


class TicketDetailBreadcrumbsTests(TestCase):
    """Breadcrumbs on the ticket detail page are derived from the viewer's
    relationship to the ticket. The view renders the trail into
    #main-breadcrumbs (after an automatic Home crumb):

      * the owner gets their personal "My Questions" trail, UNLESS they
        navigated in from the group ticket pool (detected via the Referer
        header), in which case they get the group trail instead;
      * a non-owner who can view the ticket (org teammate, moderator, staff)
        always gets the group trail, regardless of the Referer;
      * everyone else (e.g. staff on a stranger's personal ticket) gets just
        the unlinked ticket subject.
    """

    def setUp(self):
        self.owner = UserFactory()
        self.ticket = SupportTicketFactory(user=self.owner)

    def _get(self, user, referer=None):
        self.client.force_login(user)
        extra = {"HTTP_REFERER": referer} if referer is not None else {}
        return self.client.get(
            reverse("customercare.ticket_detail", args=[self.owner.username, self.ticket.id]),
            **extra,
        )

    def _breadcrumbs(self, response):
        self.assertEqual(200, response.status_code)
        return pq(response.content)("#main-breadcrumbs")

    def _group_pool_url(self):
        """Locale-prefixed group ticket pool URL, matching exactly what the
        view builds (and compares the Referer against)."""
        return reverse_locale("groups.tickets", args=[self.ticket.org_group.slug])

    def assertMyQuestionsTrail(self, response):
        crumbs = self._breadcrumbs(response)
        hrefs = [a.attrib["href"] for a in crumbs("a")]
        self.assertIn("My Questions", crumbs.text())
        self.assertTrue(
            any(reverse("users.questions", args=[self.owner.username]) in h for h in hrefs),
            f"expected a My Questions link, got {hrefs}",
        )
        # Not the group trail.
        self.assertNotIn("Groups", crumbs.text())
        self.assertNotIn("Tickets", crumbs.text())

    def assertGroupPoolTrail(self, response):
        crumbs = self._breadcrumbs(response)
        hrefs = [a.attrib["href"] for a in crumbs("a")]
        self.assertIn("Tickets", crumbs.text())
        self.assertTrue(
            any(self._group_pool_url() in h for h in hrefs),
            f"expected a group ticket pool link, got {hrefs}",
        )
        # Group trail starts at the Groups list, not the owner's questions.
        self.assertIn("Groups", crumbs.text())
        self.assertNotIn("My Questions", crumbs.text())

    def assertSubjectOnlyTrail(self, response):
        crumbs = self._breadcrumbs(response)
        self.assertIn(self.ticket.subject, crumbs.text())
        self.assertNotIn("My Questions", crumbs.text())
        self.assertNotIn("Groups", crumbs.text())
        self.assertNotIn("Tickets", crumbs.text())

    # --- owner of a personal (non-org) ticket -------------------------------

    def test_owner_personal_ticket_gets_my_questions(self):
        self.assertMyQuestionsTrail(self._get(self.owner))

    # --- owner who is also an org agent -------------------------------------

    def test_owner_agent_without_referer_gets_my_questions(self):
        """An owner who also happens to be an org agent still defaults to their
        own questions trail when they did not arrive from the group pool."""
        _make_viewable_by_teammate(self.owner, self.ticket)
        self.ticket.refresh_from_db()
        self.assertMyQuestionsTrail(self._get(self.owner))

    def test_owner_agent_from_group_pool_gets_group_trail(self):
        """The design change: an owner who navigated in from the group ticket
        pool (per the Referer) sees the group trail instead of My Questions."""
        _make_viewable_by_teammate(self.owner, self.ticket)
        self.ticket.refresh_from_db()
        response = self._get(self.owner, referer=self._group_pool_url())
        self.assertGroupPoolTrail(response)

    def test_owner_agent_with_unrelated_referer_gets_my_questions(self):
        """Only the group pool Referer flips the owner's trail; arriving from
        any other page keeps the personal trail."""
        _make_viewable_by_teammate(self.owner, self.ticket)
        self.ticket.refresh_from_db()
        elsewhere = reverse_locale("users.questions", args=[self.owner.username])
        self.assertMyQuestionsTrail(self._get(self.owner, referer=elsewhere))

    # --- non-owner viewers ---------------------------------------------------

    def test_org_agent_gets_group_trail(self):
        """A teammate who can view someone else's org ticket gets the group
        trail without any Referer."""
        teammate = _make_viewable_by_teammate(self.owner, self.ticket)
        self.ticket.refresh_from_db()
        self.assertGroupPoolTrail(self._get(teammate))

    def test_org_agent_referer_is_ignored(self):
        """The Referer gate applies only to the owner: a non-owner agent gets
        the group trail even when they arrived from an unrelated page."""
        teammate = _make_viewable_by_teammate(self.owner, self.ticket)
        self.ticket.refresh_from_db()
        elsewhere = reverse_locale("users.questions", args=[self.owner.username])
        self.assertGroupPoolTrail(self._get(teammate, referer=elsewhere))

    def test_staff_on_org_ticket_gets_group_trail(self):
        """Staff can view any ticket; on an org ticket they get the group trail
        (they pass can_view_tickets without org membership)."""
        _make_viewable_by_teammate(self.owner, self.ticket)
        self.ticket.refresh_from_db()
        staff = UserFactory(is_staff=True)
        self.assertGroupPoolTrail(self._get(staff))

    def test_staff_on_personal_ticket_gets_subject_only(self):
        """Staff viewing a stranger's personal (non-org) ticket gets just the
        subject: no personal trail (not theirs) and no group trail (no org)."""
        staff = UserFactory(is_staff=True)
        self.assertSubjectOnlyTrail(self._get(staff))
