import base64
import hashlib
import hmac
import json
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_POST
from zenpy.lib.exception import APIException

from kitsune.customercare.forms import SupportTicketReplyForm
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tasks import process_zendesk_update
from kitsune.customercare.utils import generate_classification_tags, sync_ticket_from_zendesk
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.products.models import Topic

log = logging.getLogger("k.customercare")

ACTIVE_ZD_STATUSES = {
    SupportTicket.ZD_STATUS_OPEN,
    SupportTicket.ZD_STATUS_PENDING,
    SupportTicket.ZD_STATUS_WAITING,
}

# Per-HTTP-request timeout for the user-facing reply POST. Bounds worst-case wall time
# at ~2x this (first-time replier triggers an extra create_user call).
ZENDESK_REPLY_TIMEOUT = 10

# HTTP statuses where retrying without a body change can't help.
PERMANENT_ZENDESK_HTTP_CODES = {400, 401, 403, 404, 422}


def _is_permanent_zendesk_error(exc):
    """True if retrying the same submission won't help."""
    if isinstance(exc, ValueError):
        return True
    if isinstance(exc, APIException):
        code = getattr(getattr(exc, "response", None), "status_code", None)
        return code in PERMANENT_ZENDESK_HTTP_CODES
    return False


def _ticket_needs_sync(ticket):
    if not ticket.zendesk_ticket_id:
        return False
    if ticket.last_synced_at is None:
        return True
    threshold = timedelta(seconds=settings.ZENDESK_COMMENTS_SYNC_THRESHOLD)
    return ticket.last_synced_at < timezone.now() - threshold


def _user_can_reply(user, ticket):
    if not user.is_authenticated:
        return False
    if ticket.zd_status not in ACTIVE_ZD_STATUSES:
        return False
    return (user.id == ticket.user_id) or user.has_perm("customercare.change_supportticket")


def _replies_context(ticket, viewer, reply_form=None, sync_error=False, post_error=None):
    return {
        "ticket": ticket,
        "sync_error": sync_error,
        "post_error": post_error,
        "reply_form": reply_form or SupportTicketReplyForm(),
        "can_reply": _user_can_reply(viewer, ticket),
    }


def _extract_new_comment(ticket_audit):
    """Return the new comment-event dict from a TicketAudit, or None.

    Real shape: ticket_audit.audit.events is a list of dicts. Each event has
    fields like {id, type, author_id, body, public, ...}.
    """
    events = getattr(getattr(ticket_audit, "audit", None), "events", None) or []
    return next(
        (
            ev
            for ev in events
            if isinstance(ev, dict) and ev.get("type") == "Comment" and ev.get("id")
        ),
        None,
    )


def _append_reply_to_mirror(ticket, new_comment, created_at, author):
    """Append a newly-posted reply to ticket.comments under a row lock.

    Returns the freshly-reread ticket so the caller can render with the latest
    mirror state. The lock + dedup guard make this safe against a concurrent
    Zendesk webhook for the same comment id arriving via process_zendesk_update.
    """
    mirror = {
        "id": new_comment["id"],
        "body": new_comment.get("body", ""),
        "created_at": created_at,
        "public": True,
        "author": {
            "name": author.profile.display_name,
            "id": int(author.profile.zendesk_id) if author.profile.zendesk_id else None,
        },
    }
    with transaction.atomic():
        fresh = (
            SupportTicket.objects.select_for_update(of=("self",))
            .select_related("product", "topic", "user")
            .get(id=ticket.id)
        )
        if not any(c.get("id") == new_comment["id"] for c in fresh.comments):
            fresh.comments.append(mirror)
            fresh.save(update_fields=["comments"])
    return fresh


def _render_replies(request, ticket, is_htmx, reply_form=None, post_error=None):
    """Render the replies partial (HTMX) or the full ticket page. No sync."""
    context = _replies_context(ticket, request.user, reply_form=reply_form, post_error=post_error)
    if is_htmx:
        return render(request, "customercare/includes/ticket_replies.html", context)
    return render(
        request,
        "customercare/ticket_detail.html",
        {"needs_sync": False, **context},
    )


def _handle_reply_post(request, ticket, is_htmx):
    """Synchronously post a reply to Zendesk and append to the mirror on success.

    NOTE: there's a rare ambiguous-failure window where Zendesk accepts the comment
    but our request gives up (e.g. read timeout). A user retry could double-post.
    Accepted iteration-1 risk; a Zendesk-side idempotency token would close it.
    """
    if not _user_can_reply(request.user, ticket):
        return _render_replies(request, ticket, is_htmx)

    form = SupportTicketReplyForm(request.POST)
    if not form.is_valid():
        return _render_replies(request, ticket, is_htmx, reply_form=form)

    body = form.cleaned_data["body"]
    try:
        ticket_audit = ZendeskClient(timeout=ZENDESK_REPLY_TIMEOUT).add_ticket_comment(
            user=request.user,
            ticket_id=ticket.zendesk_ticket_id,
            comment_body=body,
            public=True,
        )
    except (APIException, requests.exceptions.RequestException, ValueError) as exc:
        log.exception(f"Failed to post reply to Zendesk ticket {ticket.zendesk_ticket_id}")
        if _is_permanent_zendesk_error(exc):
            post_error = _("Sorry, your reply couldn't be posted. Please contact support.")
        else:
            post_error = _("Something went wrong. Please try again.")
        return _render_replies(request, ticket, is_htmx, reply_form=form, post_error=post_error)

    new_comment = _extract_new_comment(ticket_audit)
    if new_comment is None:
        log.warning(f"Zendesk audit had no comment event for ticket {ticket.zendesk_ticket_id}")
    else:
        ticket = _append_reply_to_mirror(
            ticket,
            new_comment=new_comment,
            created_at=ticket_audit.ticket.updated_at,
            author=request.user,
        )

    if is_htmx:
        return render(
            request,
            "customercare/includes/ticket_replies.html",
            _replies_context(ticket, request.user),
        )
    return redirect(
        "customercare.ticket_detail",
        username=ticket.user.username,
        ticket_id=ticket.id,
    )


@login_required
def ticket_detail(request, username, ticket_id):
    ticket = get_object_or_404(
        SupportTicket.objects.select_related("product", "topic", "user"),
        id=ticket_id,
        user__username=username,
    )
    is_owner = ticket.user_id == request.user.id
    if not (is_owner or request.user.has_perm("customercare.change_supportticket")):
        raise Http404

    is_htmx = bool(request.headers.get("HX-Request"))

    if request.method == "POST":
        return _handle_reply_post(request, ticket, is_htmx)

    if is_htmx:
        sync_error = False
        if _ticket_needs_sync(ticket):
            try:
                sync_ticket_from_zendesk(ticket)
            except (APIException, requests.exceptions.RequestException):
                log.exception("Failed to sync ticket %s from Zendesk", ticket.zendesk_ticket_id)
                sync_error = True
        return render(
            request,
            "customercare/includes/ticket_replies.html",
            _replies_context(ticket, request.user, sync_error=sync_error),
        )

    return render(
        request,
        "customercare/ticket_detail.html",
        {
            "needs_sync": _ticket_needs_sync(ticket),
            **_replies_context(ticket, request.user),
        },
    )


@require_POST
@permission_required("customercare.change_supportticket")
def update_topic(request, ticket_id):
    """Update topic for a support ticket."""
    ticket = get_object_or_404(SupportTicket, pk=ticket_id)

    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"error": "AJAX required"}, status=400)

    data = json.loads(request.body)
    new_topic_id = data.get("topic")

    try:
        new_topic = Topic.objects.get(id=new_topic_id, products=ticket.product)
    except Topic.DoesNotExist:
        return JsonResponse({"error": "Topic not found"}, status=404)

    ticket.topic = new_topic
    ticket.save(update_fields=["topic"])

    # Regenerate tags from new topic
    system_tags = [
        tag for tag in ticket.zendesk_tags if tag in ["loginless_ticket", "stage", "other"]
    ]
    classification_tags = generate_classification_tags(
        ticket, {"topic_result": {"topic": new_topic.title}}
    )
    ticket.zendesk_tags = system_tags + classification_tags
    ticket.save(update_fields=["zendesk_tags"])

    return JsonResponse({"updated_topic": str(new_topic)})


class ZendeskWebhookView(View):
    """Receive push notifications from Zendesk via webhooks.

    Authentication is two-layered:
    1. API key — Zendesk sends a configurable header with a shared key.
    2. HMAC-SHA256 signature — verifies payload integrity and authenticity.
    """

    @staticmethod
    def verify_api_key(request):
        """Verify the API key sent by Zendesk in a custom header."""
        api_key = request.headers.get(settings.ZENDESK_WEBHOOK_API_KEY_HEADER_NAME)

        if not (api_key and hmac.compare_digest(api_key, settings.ZENDESK_WEBHOOK_API_KEY)):
            raise SuspiciousOperation("Invalid or missing Zendesk webhook API key.")

    @staticmethod
    def verify_signature(request):
        """Verify the HMAC-SHA256 signature from Zendesk.

        Zendesk computes the signature over: timestamp + body.
        """
        signature_header = request.headers.get("x-zendesk-webhook-signature")
        timestamp = request.headers.get("x-zendesk-webhook-signature-timestamp")

        if not (signature_header and timestamp):
            raise SuspiciousOperation("Missing signature or timestamp header.")

        secret = settings.ZENDESK_WEBHOOK_SIGNING_SECRET.encode("utf-8")
        message = timestamp.encode("utf-8") + request.body
        computed = hmac.new(secret, message, hashlib.sha256).digest()
        try:
            expected = base64.b64decode(signature_header)
        except ValueError:
            raise SuspiciousOperation("Malformed Zendesk webhook signature.")

        if not hmac.compare_digest(computed, expected):
            raise SuspiciousOperation("Invalid Zendesk webhook signature.")

    def post(self, request, *args, **kwargs):
        try:
            self.verify_api_key(request)
            self.verify_signature(request)
        except SuspiciousOperation:
            log.warning("Zendesk webhook authentication failed.")
            return HttpResponse(status=403)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        if not payload:
            return HttpResponse(status=400)

        process_zendesk_update.delay(payload)
        return HttpResponse(status=200)
