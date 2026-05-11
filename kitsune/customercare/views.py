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
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from zenpy.lib.exception import APIException

from kitsune.customercare.forms import SupportTicketReplyForm
from kitsune.customercare.models import SupportTicket, SupportTicketReplyOutbox
from kitsune.customercare.tasks import post_outbox_reply, process_zendesk_update
from kitsune.customercare.utils import generate_classification_tags, sync_ticket_from_zendesk
from kitsune.products.models import Topic

log = logging.getLogger("k.customercare")


ACTIVE_ZD_STATUSES = {
    SupportTicket.ZD_STATUS_OPEN,
    SupportTicket.ZD_STATUS_PENDING,
    SupportTicket.ZD_STATUS_WAITING,
}


def _ticket_needs_sync(ticket):
    if not ticket.zendesk_ticket_id:
        return False
    if ticket.last_synced_at is None:
        return True
    threshold = timedelta(seconds=settings.ZENDESK_COMMENTS_SYNC_THRESHOLD)
    return ticket.last_synced_at < timezone.now() - threshold


def _user_can_reply(user, ticket):
    return (
        user.is_authenticated
        and user.id == ticket.user_id
        and ticket.zd_status in ACTIVE_ZD_STATUSES
    )


def _replies_context(ticket, viewer, reply_form=None, sync_error=False):
    outbox_entries = list(SupportTicketReplyOutbox.objects.unconfirmed_for(ticket))
    has_pending_outbox = any(
        o.status == SupportTicketReplyOutbox.STATUS_PENDING for o in outbox_entries
    )
    return {
        "ticket": ticket,
        "sync_error": sync_error,
        "reply_form": reply_form or SupportTicketReplyForm(),
        "can_reply": _user_can_reply(viewer, ticket),
        "outbox_entries": outbox_entries,
        "has_pending_outbox": has_pending_outbox,
    }


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
        if not is_owner:
            return HttpResponseForbidden()
        if ticket.zd_status not in ACTIVE_ZD_STATUSES:
            return HttpResponseBadRequest()

        form = SupportTicketReplyForm(request.POST)
        if not form.is_valid():
            context = _replies_context(ticket, request.user, reply_form=form)
            if is_htmx:
                return render(request, "customercare/includes/ticket_replies.html", context)
            return render(
                request,
                "customercare/ticket_detail.html",
                {"needs_sync": False, **context},
            )

        outbox = SupportTicketReplyOutbox.objects.create(
            ticket=ticket,
            author=request.user,
            body=form.cleaned_data["body"],
        )
        post_outbox_reply.delay(outbox.id)

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
        {"needs_sync": _ticket_needs_sync(ticket), **_replies_context(ticket, request.user)},
    )


@login_required
@require_POST
def retry_outbox_reply(request, ticket_id, outbox_id):
    # Relies on ATOMIC_REQUESTS=True for the ambient transaction.
    # SELECT FOR UPDATE locks the row before the status check so two concurrent
    # retries can't both flip `failed` -> `pending` and double-dispatch the post
    # task; the second request blocks on the SELECT, then sees `pending` and aborts.
    # `of=("self",)` locks only the outbox row — needed because select_related
    # pulls in SupportTicket.user via LEFT JOIN (nullable FK), which PostgreSQL
    # refuses to lock with a plain FOR UPDATE.
    outbox = get_object_or_404(
        SupportTicketReplyOutbox.objects.select_for_update(of=("self",)).select_related(
            "ticket", "ticket__user"
        ),
        id=outbox_id,
        ticket_id=ticket_id,
    )
    if outbox.ticket.user_id != request.user.id or outbox.author_id != request.user.id:
        raise Http404
    if outbox.status != SupportTicketReplyOutbox.STATUS_FAILED:
        return HttpResponseBadRequest()
    if outbox.ticket.zd_status not in ACTIVE_ZD_STATUSES:
        return HttpResponseBadRequest()

    outbox.status = SupportTicketReplyOutbox.STATUS_PENDING
    outbox.error_reason = ""
    outbox.attempt_count = 0
    outbox.save(update_fields=["status", "error_reason", "attempt_count", "updated_at"])

    # Dispatch only after the row write commits — if the transaction rolls back,
    # no task is queued.
    transaction.on_commit(lambda: post_outbox_reply.delay(outbox.id))

    if request.headers.get("HX-Request"):
        return render(
            request,
            "customercare/includes/ticket_replies.html",
            _replies_context(outbox.ticket, request.user),
        )
    return redirect(
        "customercare.ticket_detail",
        username=outbox.ticket.user.username,
        ticket_id=outbox.ticket.id,
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
