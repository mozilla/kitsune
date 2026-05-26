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
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST
from zenpy.lib.exception import APIException

from kitsune.customercare.forms import SupportTicketReplyForm
from kitsune.customercare.models import SupportTicket, SupportTicketPendingChange
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


@login_required
@require_http_methods(["GET", "POST"])
def ticket_detail(request, username, ticket_id):
    ticket = get_object_or_404(
        SupportTicket.objects.accessible_to(request.user).select_related(
            "product", "topic", "user", "org_group"
        ),
        id=ticket_id,
        user__username=username,
    )

    pending = ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)

    initial = (
        {"body": pending.payload}
        if pending and pending.effective_status == SupportTicketPendingChange.STATUS_FAILED
        else None
    )

    form = SupportTicketReplyForm(request.POST or None, initial=initial)

    is_htmx = bool(request.headers.get("HX-Request"))
    # Captured before any post-submission form reset: a bound form means the
    # user is submitting; an unbound HTMX request is a background refresh.
    is_polling = is_htmx and not form.is_bound

    if form.is_valid() and (ticket.zd_status != SupportTicket.ZD_STATUS_CLOSED):
        new_body = form.cleaned_data["body"]
        should_post_reply = False
        with transaction.atomic():
            pending = ticket.pending_change(
                SupportTicketPendingChange.KIND_COMMENT, for_update=True
            )
            already_sending = pending and (
                pending.effective_status == SupportTicketPendingChange.STATUS_SENDING
            )
            same_body = pending and (pending.payload == new_body)
            if (not already_sending) and same_body:
                # Same body but trying again. Bump "last_attempted_at" so
                # stale-sending detection anchors on this retry, not the prior
                # failed attempt.
                pending.status = SupportTicketPendingChange.STATUS_SENDING
                pending.last_attempted_at = timezone.now()
                pending.save(update_fields=["status", "last_attempted_at"])
                should_post_reply = True
            elif not already_sending:
                # No prior pending, or user edited the body — start fresh.
                if pending:
                    pending.delete()
                try:
                    with transaction.atomic():
                        pending = SupportTicketPendingChange.objects.create(
                            ticket=ticket,
                            kind=SupportTicketPendingChange.KIND_COMMENT,
                            payload=new_body,
                        )
                except IntegrityError:
                    pending = ticket.pending_change(SupportTicketPendingChange.KIND_COMMENT)
                else:
                    should_post_reply = True

        if should_post_reply:
            post_reply_to_zendesk.delay(ticket_id=ticket.id)
            if not is_htmx:
                return redirect(
                    "customercare.ticket_detail",
                    username=ticket.user.username,
                    ticket_id=ticket.id,
                )

        form = SupportTicketReplyForm()

    needs_sync = _ticket_needs_sync(ticket)

    sync_error = False
    if is_polling and needs_sync:
        try:
            sync_ticket_from_zendesk(ticket)
        except APIException, requests.exceptions.RequestException:
            log.exception("Failed to sync ticket %s from Zendesk", ticket.zendesk_ticket_id)
            sync_error = True

    context = {"ticket": ticket, "pending": pending, "sync_error": sync_error, "reply_form": form}
    if is_htmx:
        return render(request, "customercare/includes/ticket_replies.html", context)
    return render(
        request,
        "customercare/ticket_detail.html",
        {**context, "needs_sync": needs_sync},
    )


@login_required
@require_http_methods(["GET", "POST"])
def ticket_status(request, username, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user__username=username)

    if request.user.id != ticket.user_id:
        raise Http404

    if request.method == "POST":
        target_status = request.POST.get("target_status")
        should_post_status = False
        with transaction.atomic():
            pending = ticket.pending_change(
                SupportTicketPendingChange.KIND_ZD_STATUS, for_update=True
            )
            already_sending = pending and (
                pending.effective_status == SupportTicketPendingChange.STATUS_SENDING
            )
            if (not already_sending) and (target_status in ticket.permitted_zd_status_targets()):
                should_post_status = True
                if pending:
                    pending.payload = target_status
                    pending.status = SupportTicketPendingChange.STATUS_SENDING
                    pending.last_attempted_at = timezone.now()
                    pending.save(update_fields=["payload", "status", "last_attempted_at"])
                else:
                    try:
                        with transaction.atomic():
                            SupportTicketPendingChange.objects.create(
                                ticket=ticket,
                                kind=SupportTicketPendingChange.KIND_ZD_STATUS,
                                payload=target_status,
                            )
                    except IntegrityError:
                        should_post_status = False

        if should_post_status:
            post_status_change_to_zendesk.delay(ticket_id=ticket.id)

    if request.headers.get("HX-Request"):
        return render(
            request,
            "customercare/includes/ticket_status.html",
            {"ticket": ticket},
        )
    return redirect("customercare.ticket_detail", username=username, ticket_id=ticket.id)


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
