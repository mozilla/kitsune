import base64
import hashlib
import hmac
import json
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.forms import SupportTicketReplyForm
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tasks import process_zendesk_update
from kitsune.customercare.utils import generate_classification_tags, sync_ticket_from_zendesk
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.products.models import Topic

log = logging.getLogger("k.customercare")

# Zendesk failures we surface as a notice rather than a 500 (ZenpyException
# covers client construction, e.g. missing credentials).
ZENDESK_ERRORS = (APIException, ZenpyException, requests.exceptions.RequestException)


def _ticket_needs_sync(ticket):
    if not ticket.zendesk_ticket_id:
        return False
    if ticket.last_synced_at is None:
        return True
    threshold = timedelta(seconds=settings.ZENDESK_COMMENTS_SYNC_THRESHOLD)
    return ticket.last_synced_at < timezone.now() - threshold


def _accessible_ticket(request, username, ticket_id, select_related=None):
    qs = SupportTicket.objects.accessible_to(request.user)
    if select_related:
        qs = qs.select_related(*select_related)
    ticket = get_object_or_404(qs, id=ticket_id, user__username=username)
    can_reply = ticket.can_reply(request.user)
    if request.method == "POST" and not can_reply:
        raise PermissionDenied
    return ticket, can_reply


def _reply_placeholder(ticket):
    return (
        _("Reply here to reopen this ticket.")
        if ticket.zd_status == SupportTicket.ZD_STATUS_SOLVED
        else None
    )


@login_required
@require_http_methods(["GET", "POST"])
def ticket_detail(request, username, ticket_id):
    ticket, can_reply = _accessible_ticket(
        request, username, ticket_id, select_related=("product", "topic", "user")
    )

    form = SupportTicketReplyForm(request.POST or None, placeholder=_reply_placeholder(ticket))

    is_htmx = bool(request.headers.get("HX-Request"))
    is_htmx_get = is_htmx and not form.is_bound

    sync_error = False
    reply_error = False
    status_changed = False

    if (ticket.zd_status != SupportTicket.ZD_STATUS_CLOSED) and form.is_valid():
        new_body = form.cleaned_data["body"]

        # Zendesk automatically triggers a reopen only when the comment author
        # is the same as the API user, which is never true in our case, so we
        # take care of that here.
        new_status = (
            SupportTicket.ZD_STATUS_OPEN
            if ticket.zd_status
            in {SupportTicket.ZD_STATUS_PENDING, SupportTicket.ZD_STATUS_SOLVED}
            else None
        )

        try:
            ticket_audit = ZendeskClient().add_ticket_comment(
                user=ticket.user,
                ticket_id=int(ticket.zendesk_ticket_id),
                comment_body=new_body,
                public=True,
                status=new_status,
            )
        except ZENDESK_ERRORS:
            log.exception("Failed to add comment to Zendesk ticket %s", ticket.zendesk_ticket_id)
            reply_error = True
        else:
            new_comment = next(
                (
                    ev
                    for ev in ticket_audit.audit.events
                    if isinstance(ev, dict) and ev.get("type") == "Comment" and ev.get("id")
                ),
                None,
            )
            if new_comment is None:
                log.error(
                    f"Zendesk audit had no comment event for ticket {ticket_audit.ticket.id}."
                )
                reply_error = True

        if not reply_error:
            with transaction.atomic():
                ticket = (
                    SupportTicket.objects.select_related("user", "user__profile")
                    .select_for_update(of=("self",))
                    .get(id=ticket_id)
                )

                ticket.zd_updated_at = parse_datetime(ticket_audit.ticket.updated_at)
                update_fields = ["zd_updated_at"]

                if ticket.zd_status != ticket_audit.ticket.status.lower():
                    ticket.zd_status = ticket_audit.ticket.status.lower()
                    update_fields.append("zd_status")
                    status_changed = True

                new_comment_id = new_comment["id"]
                if not any(c.get("id") == new_comment_id for c in ticket.comments):
                    ticket.comments.append(
                        {
                            "id": new_comment_id,
                            "body": new_comment["html_body"],
                            "created_at": ticket_audit.ticket.updated_at,
                            "public": True,
                            "author": {
                                "name": ticket.user.profile.display_name,
                                "id": new_comment["author_id"],
                            },
                        }
                    )
                    update_fields.append("comments")

                ticket.save(update_fields=update_fields)

            form = SupportTicketReplyForm()

            if not is_htmx:
                return redirect(
                    "customercare.ticket_detail",
                    username=ticket.user.username,
                    ticket_id=ticket.id,
                )

    needs_sync = _ticket_needs_sync(ticket)

    if is_htmx_get and needs_sync:
        try:
            sync_ticket_from_zendesk(ticket)
        except ZENDESK_ERRORS:
            log.exception("Failed to sync ticket %s from Zendesk", ticket.zendesk_ticket_id)
            sync_error = True

    context = {
        "ticket": ticket,
        "reply_form": form,
        "sync_error": sync_error,
        "reply_error": reply_error,
        "status_changed": status_changed,
        "can_reply": can_reply,
    }
    if is_htmx:
        return render(request, "customercare/includes/ticket_replies.html", context)
    return render(
        request,
        "customercare/ticket_detail.html",
        {**context, "needs_sync": needs_sync},
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
