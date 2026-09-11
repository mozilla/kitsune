import base64
import hashlib
import hmac
import json
import logging
from datetime import timedelta

import jwt
import requests
import waffle
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, SuspiciousOperation
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _
from django.utils.translation import pgettext
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST
from zenpy.lib.exception import APIException, RecordNotFoundException, ZenpyException

from kitsune.customercare.forms import SupportTicketReplyForm
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tasks import process_zendesk_update
from kitsune.customercare.utils import generate_classification_tags, sync_ticket_from_zendesk
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.groups.templatetags.jinja_helpers import group_breadcrumbs
from kitsune.journal.models import Record
from kitsune.products.models import Product, Topic
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import is_ratelimited

log = logging.getLogger("k.customercare")

# Zendesk failures we surface as a notice rather than a 500 (ZenpyException
# covers client construction, e.g. missing credentials).
ZENDESK_ERRORS = (APIException, ZenpyException, requests.exceptions.RequestException)

CHAT_JOURNAL_SRC = "customercare.chat"


def _ticket_needs_sync(ticket):
    if not ticket.is_syncable:
        return False
    if ticket.last_synced_at is None:
        return True
    threshold = timedelta(seconds=settings.ZENDESK_COMMENTS_SYNC_THRESHOLD)
    return ticket.last_synced_at < timezone.now() - threshold


def _reply_placeholder(ticket):
    return (
        _("Reply here to reopen this ticket.")
        if ticket.zd_status == SupportTicket.ZD_STATUS_SOLVED
        else None
    )


def chat_jwt_is_ratelimited(request):
    """Apply every window; return True if any is exceeded.

    Deliberately not short-circuited, so the wider windows keep counting.
    """
    limited = False
    for rate in settings.ZENDESK_CHAT_RATELIMITS:
        if is_ratelimited(request, "support-chat-jwt", rate):
            limited = True
    return limited


@require_POST
@never_cache
def chat_jwt(request, product_slug):
    """Sign a short-lived token that identifies the requesting user to Zendesk.

    The messaging widget posts here whenever it needs to prove the requesting
    user's identity, including when its previous token expires. POST rather than
    GET so Django's CSRF middleware runs, which checks both the CSRF token and
    the Origin header.
    """
    if not waffle.switch_is_active("zendesk-chat"):
        return HttpResponse(status=404)

    if not (settings.ZENDESK_CHAT_SIGNING_SECRET and settings.ZENDESK_CHAT_SIGNING_KEY_ID):
        raise ImproperlyConfigured("Support chat requires a signing key and secret.")

    user = request.user

    if not user.is_authenticated:
        return HttpResponse(status=401)

    if chat_jwt_is_ratelimited(request):
        return HttpResponse(status=429)

    profile = user.profile
    external_id = profile.fxa_uid

    if not external_id:
        Record.objects.error(
            CHAT_JOURNAL_SRC,
            "user {username} (#{user_id}) has no fxa_uid",
            username=user.username,
            user_id=user.id,
        )
        return HttpResponse(status=401)

    # Slug is user-supplied, so keep it short enough for the journal message.
    product = Product.active.filter(slug=product_slug).first()
    if product is None:
        Record.objects.info(
            CHAT_JOURNAL_SRC,
            "user {username} (#{user_id}) asked for chat on unknown product {slug}",
            username=user.username,
            user_id=user.id,
            slug=product_slug[:50],
        )
        return HttpResponse(status=404)

    # TODO: Replace with eligibility check.
    is_eligible_for_chat = True

    if not is_eligible_for_chat:
        Record.objects.info(
            CHAT_JOURNAL_SRC,
            "user {username} (#{user_id}) is not eligible for chat on {slug}",
            username=user.username,
            user_id=user.id,
            slug=product.slug,
        )
        return HttpResponse(status=403)

    token = jwt.encode(
        {
            "scope": "user",
            "external_id": external_id,
            "name": profile.display_name,
            "email": user.email,
            "email_verified": True,
            "exp": timezone.now() + timedelta(seconds=settings.ZENDESK_CHAT_JWT_LIFETIME),
        },
        settings.ZENDESK_CHAT_SIGNING_SECRET,
        algorithm="HS256",
        headers={"kid": settings.ZENDESK_CHAT_SIGNING_KEY_ID},
    )

    if waffle.switch_is_active("record-chat-token-issuance"):
        Record.objects.info(
            CHAT_JOURNAL_SRC,
            "user {username} (#{user_id}) was issued a chat token for {slug}",
            username=user.username,
            user_id=user.id,
            slug=product.slug,
        )

    return HttpResponse(token, content_type="text/plain")


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

    can_reply = ticket.can_reply(request.user)
    if request.method != "GET" and not can_reply:
        raise PermissionDenied

    form = SupportTicketReplyForm(request.POST or None, placeholder=_reply_placeholder(ticket))

    is_htmx = bool(request.headers.get("HX-Request"))
    is_htmx_get = is_htmx and not form.is_bound

    sync_error = False
    reply_error = False
    status_changed = False

    if (
        (ticket.zd_status != SupportTicket.ZD_STATUS_CLOSED)
        and ticket.is_syncable
        and form.is_valid()
    ):
        set_zd_deleted_at = False

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
                comment_body=form.cleaned_data["body"],
                public=True,
                status=new_status,
            )
        except RecordNotFoundException:
            # The Zendesk ticket was deleted between the time the support ticket was
            # acquired and the "add_ticket_comment" call above. Let's set "zd_deleted_at"
            # just in case the deletion event never arrives via the webhook.
            set_zd_deleted_at = True
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

                if set_zd_deleted_at:
                    ticket.zd_deleted_at = timezone.now()
                    update_fields = ["zd_deleted_at"]
                    status_changed = True
                else:
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
            old_status = ticket.zd_status
            ticket = sync_ticket_from_zendesk(ticket)
        except ZENDESK_ERRORS:
            log.exception("Failed to sync ticket %s from Zendesk", ticket.zendesk_ticket_id)
            sync_error = True
        else:
            status_changed = (ticket.zd_status != old_status) or not ticket.is_syncable

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

    # Determine the proper breadcrumbs.
    crumbs = [(None, ticket.subject)]
    is_owner = request.user.id == ticket.user_id
    has_group = bool(ticket.org_group)

    show_group_crumbs = False
    if has_group:
        url_group_tickets = reverse("groups.tickets", args=[ticket.org_group.slug])
        if is_owner:
            # Owner only gets group crumbs if they explicitly came from the group URL.
            show_group_crumbs = url_group_tickets in request.headers.get("referer", "")
        else:
            # Non-owners get group crumbs if they have permission.
            show_group_crumbs = ticket.org_group.can_view_tickets(request.user)

    if show_group_crumbs:
        crumbs = [
            *group_breadcrumbs(ticket.org_group),
            (url_group_tickets, _("Tickets")),
            *crumbs,
        ]
    elif is_owner:
        crumbs = [
            (reverse("users.questions", args=[ticket.user.username]), _("My Questions")),
            *crumbs,
        ]

    return render(
        request,
        "customercare/ticket_detail.html",
        {
            **context,
            "needs_sync": needs_sync,
            "crumbs": crumbs,
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

    return JsonResponse({"updated_topic": pgettext("DB: products.Topic.title", new_topic.title)})


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
