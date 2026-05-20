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
from django.views import View
from django.views.decorators.http import require_POST
from zenpy.lib.exception import APIException

from kitsune.customercare.forms import SupportTicketReplyForm
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tasks import (
    post_reply_to_zendesk,
    post_status_change_to_zendesk,
    process_zendesk_update,
)
from kitsune.customercare.utils import generate_classification_tags, sync_ticket_from_zendesk
from kitsune.products.models import Topic

log = logging.getLogger("k.customercare")


def _ticket_needs_sync(ticket):
    if not ticket.zendesk_ticket_id:
        return False
    if ticket.last_synced_at is None:
        return True
    threshold = timedelta(seconds=settings.ZENDESK_COMMENTS_SYNC_THRESHOLD)
    return ticket.last_synced_at < timezone.now() - threshold


def _replies_context(ticket, reply_form=None, sync_error=False):
    if reply_form is None:
        pending = ticket.effective_pending("comment")
        initial = (
            {"body": pending["body"]} if pending and pending.get("status") == "failed" else None
        )
        reply_form = SupportTicketReplyForm(initial=initial)
    return {
        "ticket": ticket,
        "sync_error": sync_error,
        "reply_form": reply_form,
    }


def _render_replies(request, ticket, is_htmx, reply_form=None):
    """Render the replies partial (HTMX) or the full ticket page. No sync."""
    context = _replies_context(ticket, reply_form=reply_form)
    if is_htmx:
        return render(request, "customercare/includes/ticket_replies.html", context)
    return render(
        request,
        "customercare/ticket_detail.html",
        {"needs_sync": False, **context},
    )


@login_required
def ticket_detail(request, username, ticket_id):
    ticket = get_object_or_404(
        SupportTicket.objects.select_related("product", "topic", "user"),
        id=ticket_id,
        user__username=username,
    )

    if not (
        ticket.user_id == request.user.id
        or request.user.has_perm("customercare.change_supportticket")
    ):
        raise Http404

    is_htmx = bool(request.headers.get("HX-Request"))

    if request.method == "POST":
        # Only the ticket owner can reply. Staff with view permission can read
        # the ticket but can't post on the owner's behalf.
        if request.user.id != ticket.user_id:
            raise Http404

        form = SupportTicketReplyForm(request.POST)
        if not form.is_valid():
            return _render_replies(request, ticket, is_htmx, reply_form=form)

        new_body = form.cleaned_data["body"]
        with transaction.atomic():
            ticket = (
                SupportTicket.objects.select_for_update(of=("self",))
                .select_related("product", "topic", "user")
                .get(id=ticket.id)
            )
            pending = ticket.effective_pending("comment")
            if pending and pending.get("status") == "sending":
                # A task is currently working on a prior submission. Re-render the
                # current state; the form is disabled in the UI for this case.
                return _render_replies(request, ticket, is_htmx)
            elif pending and new_body == pending["body"]:
                # Re-attempt the existing pending.
                ticket.pending_changes["comment"] = {
                    **ticket.pending_changes["comment"],
                    "status": "sending",
                }
                ticket.pending_changes["comment"].pop("allow_retries", None)
                ticket.save(update_fields=["pending_changes"])
            else:
                # No prior pending, or user changed the body — create fresh.
                ticket.pending_changes["comment"] = {
                    "body": new_body,
                    "status": "sending",
                    "created_at": timezone.now().isoformat(),
                    "last_attempted_at": None,
                }
                ticket.save(update_fields=["pending_changes"])

        post_reply_to_zendesk.delay(ticket_id=ticket.id)

        if is_htmx:
            return render(
                request,
                "customercare/includes/ticket_replies.html",
                _replies_context(ticket),
            )
        return redirect(
            "customercare.ticket_detail",
            username=ticket.user.username,
            ticket_id=ticket.id,
        )

    if is_htmx:
        sync_error = False
        if _ticket_needs_sync(ticket):
            try:
                sync_ticket_from_zendesk(ticket)
            except APIException, requests.exceptions.RequestException:
                log.exception("Failed to sync ticket %s from Zendesk", ticket.zendesk_ticket_id)
                sync_error = True
        return render(
            request,
            "customercare/includes/ticket_replies.html",
            _replies_context(ticket, sync_error=sync_error),
        )

    return render(
        request,
        "customercare/ticket_detail.html",
        {
            "needs_sync": _ticket_needs_sync(ticket),
            **_replies_context(ticket),
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


@login_required
def ticket_status(request, username, ticket_id):
    """POST accepts a status-change request from the ticket owner and enqueues
    the Zendesk update. GET re-renders the status partial (used by HTMX polling
    while a change is in flight). Both methods return the `ticket_status.html`
    partial for HTMX clients and redirect to the ticket detail page otherwise.
    """
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user__username=username)

    if request.user.id != ticket.user_id:
        raise Http404

    if request.method == "POST":
        target_status = request.POST.get("target_status")
        enqueue_task = False
        with transaction.atomic():
            ticket = SupportTicket.objects.select_for_update().get(id=ticket.id)
            if target_status in ticket.permitted_zd_status_targets():
                ticket.pending_changes["zd_status"] = {
                    "target_status": target_status,
                    "status": "sending",
                    "created_at": timezone.now().isoformat(),
                    "last_attempted_at": None,
                }
                ticket.save(update_fields=["pending_changes"])
                enqueue_task = True
            # If the target is invalid or no longer permitted, fall through and
            # re-render the current state — the UI will reflect what's actually
            # available now.

        # Enqueue after the transaction commits — otherwise the worker can pick
        # up the task and read the row before the pending entry is visible,
        # leading to a no-op task and a stuck "sending" state.
        if enqueue_task:
            post_status_change_to_zendesk.delay(ticket_id=ticket.id)

    if request.headers.get("HX-Request"):
        return render(request, "customercare/includes/ticket_status.html", {"ticket": ticket})
    return redirect("customercare.ticket_detail", username=username, ticket_id=ticket.id)


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
