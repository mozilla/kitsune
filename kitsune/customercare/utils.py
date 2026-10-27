import logging
from dataclasses import dataclass
from typing import Any

import waffle
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from zenpy.lib.exception import APIException, RecordNotFoundException

from kitsune.customercare.models import (
    MissingTicketContext,
    SupportTicket,
    TicketHeld,
    ZendeskOrganization,
)
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.groups.models import GroupProfile
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.products.models import (
    Product,
    ProductSupportConfig,
    SupportOrganization,
    Topic,
)
from kitsune.questions.utils import flag_object
from kitsune.users.models import Profile

log = logging.getLogger("k.customercare")

# The channel of comments in which Zendesk records a live chat's messages, in batches.
CHAT_TRANSCRIPT_CHANNEL = "chat_transcript"


@dataclass(frozen=True)
class ChatEligibility:
    org: SupportOrganization | None = None
    reason: str | None = None
    conflicting_orgs: tuple[SupportOrganization, ...] = ()

    @property
    def eligible(self) -> bool:
        return self.org is not None

    @property
    def disabled_site_wide(self) -> bool:
        return self.reason == "chat_is_disabled"


def resolve_chat_eligibility(user, product: Product) -> ChatEligibility:
    """Require one chat-enabled organization so ticket ownership is unambiguous."""
    if not waffle.switch_is_active("zendesk-chat"):
        return ChatEligibility(reason="chat_is_disabled")

    if not (
        settings.ZENDESK_CHAT_WIDGET_KEY
        and settings.ZENDESK_CHAT_SIGNING_SECRET
        and settings.ZENDESK_CHAT_SIGNING_KEY_ID
    ):
        return ChatEligibility(reason="chat_not_configured")

    if not (user and user.is_authenticated):
        return ChatEligibility(reason="not_authenticated")
    if not user.is_active:
        return ChatEligibility(reason="inactive_user")
    if product.is_archived:
        return ChatEligibility(reason="product_unavailable")

    config = ProductSupportConfig.objects.active_for(product)
    if config is None or config.zendesk_config is None:
        return ChatEligibility(reason="no_ticketing_support")
    if not config.admits(user):
        return ChatEligibility(reason="subscription_required")

    organizations = list(config.support_organizations.containing(user))
    chat_orgs = tuple(org for org in organizations if org.include_live_chat)
    match chat_orgs:
        case []:
            reason = "org_without_chat" if organizations else "no_entitled_org"
            return ChatEligibility(reason=reason)
        case [org]:
            return ChatEligibility(org=org)
        case _:
            return ChatEligibility(reason="ambiguous_multi_org", conflicting_orgs=chat_orgs)


def fetch_zendesk_ticket_data(zendesk_ticket_id: str):
    """Fetch ticket and comments from Zendesk."""
    client = ZendeskClient()
    zd_ticket = client.get_ticket(zendesk_ticket_id)
    zd_comments = client.get_ticket_comments(zendesk_ticket_id)
    return zd_ticket, zd_comments


def apply_zendesk_ticket_data(ticket: SupportTicket, zd_ticket, zd_comments) -> None:
    """Apply fetched Zendesk data to a SupportTicket and save."""
    ticket.zd_status = zd_ticket.status.lower()
    ticket.zd_updated_at = zd_ticket.updated_at
    ticket.subject = zd_ticket.subject[:255]
    ticket.description = zd_ticket.description
    ticket.comments = [
        {
            "id": c.id,
            "body": c.html_body,
            "created_at": c.created_at,
            "public": c.public,
            "is_transcript": c.via.channel == CHAT_TRANSCRIPT_CHANNEL,
            # A live chat's transcript comments have no author.
            "author": {"name": c.author.name, "id": c.author.id} if c.author else None,
        }
        for c in zd_comments
    ]
    ticket.last_synced_at = timezone.now()
    ticket.save(
        update_fields=[
            "zd_status",
            "zd_updated_at",
            "subject",
            "description",
            "comments",
            "last_synced_at",
        ]
    )


def sync_ticket_from_zendesk(ticket: SupportTicket) -> SupportTicket:
    """Fetch fresh ticket status and comments from Zendesk and save to DB.

    Returns the up-to-date ticket. The row we lock and mutate is a different
    instance than the one passed in, so callers that re-render afterwards (e.g.
    ticket_detail) must use the returned object rather than the one they passed.
    """
    if not ticket.is_syncable:
        return ticket

    set_zd_deleted_at = False

    try:
        zd_ticket, zd_comments = fetch_zendesk_ticket_data(ticket.zendesk_ticket_id)
    except RecordNotFoundException:
        # The Zendesk ticket was deleted between the time the support ticket was
        # acquired and the fetch above. Let's set "zd_deleted_at" just in case
        # the deletion event never arrives via the webhook.
        set_zd_deleted_at = True

    with transaction.atomic():
        try:
            ticket = SupportTicket.objects.select_for_update().get(id=ticket.id)
        except SupportTicket.DoesNotExist:
            return ticket

        if set_zd_deleted_at:
            ticket.zd_deleted_at = timezone.now()
            ticket.save(update_fields=["zd_deleted_at"])
        else:
            apply_zendesk_ticket_data(ticket, zd_ticket, zd_comments)

    return ticket


def create_support_ticket(
    user, product: Product, *, zd_ticket=None, coverage=None, accepted_context=None, **fields
) -> SupportTicket:
    """Create a SupportTicket.

    Without zd_ticket, it's created, saved as pending, and classified, after which it's
    sent to Zendesk. With zd_ticket, since Zendesk already has the ticket, we create a
    copy of it. Calling again with the same zd_ticket returns that copy.
    """
    # tasks imports utils to process and send tickets.
    from kitsune.customercare.tasks import zendesk_submission_classifier

    if "email" not in fields:
        fields["email"] = user.email

    if zd_ticket is None:
        if not accepted_context:
            raise ValueError("A new support ticket requires its accepted context")
        org_group = coverage.contract.company if coverage else None
        fields.update(
            origin=SupportTicket.Origin.ENTERPRISE if coverage else SupportTicket.Origin.PRODUCT,
            coverage=coverage,
            accepted_context=accepted_context,
        )
    else:
        # The organization that let the person chat, if they still can.
        eligibility = resolve_chat_eligibility(user, product)
        if eligibility.reason == "chat_not_configured":
            raise ImproperlyConfigured(
                "Chat requires a widget key, and a signing key and its secret."
            )
        org = eligibility.org
        org_group = GroupProfile.objects.filter(group_id=org.group_id).first() if org else None

    fields.update(user=user, product=product, org_group=org_group)

    if zd_ticket is None:
        ticket = SupportTicket.objects.create(
            **fields, submission_status=SupportTicket.STATUS_PENDING
        )
        zendesk_submission_classifier.delay(ticket.id)
        return ticket

    zd_comments = ZendeskClient().get_ticket_comments(zd_ticket.id)

    with transaction.atomic():
        ticket, created = SupportTicket.objects.get_or_create(
            zendesk_ticket_id=str(zd_ticket.id),
            defaults={
                **fields,
                "zd_channel": zd_ticket.via.channel,
                "submission_status": SupportTicket.STATUS_SENT,
                "created": parse_datetime(zd_ticket.created_at),
            },
        )
        if created:
            apply_zendesk_ticket_data(ticket, zd_ticket, zd_comments)

    return ticket


def adopt_chat_ticket(zd_ticket) -> SupportTicket | None:
    """Create the SupportTicket for a live chat that started in Zendesk.

    Returns None if the Zendesk ticket was not created via the SupportTicket.ZD_CHANNEL_MESSAGING
    channel, or we can't find the user who requested the ticket, or the ticket's associated
    product. Calling it again for the same chat returns the ticket that was already created.
    """
    if zd_ticket.via.channel != SupportTicket.ZD_CHANNEL_MESSAGING:
        return None

    # Find the product from the chat's product tag.
    product = None
    prefix = settings.ZENDESK_CHAT_PRODUCT_TAG_PREFIX
    for tag in zd_ticket.tags:
        if tag.startswith(prefix):
            slug = tag.removeprefix(prefix)
            product = Product.objects.filter(slug=slug).first()
            if not product:
                log.error(
                    f"Chat ticket {zd_ticket.id} has a tag for product {slug!r}, "
                    "which doesn't exist."
                )
            break

    if not product:
        return None

    # Find the SUMO user associated with the given Zendesk user id.
    try:
        zd_user = ZendeskClient().get_user(zd_ticket.requester_id)
    except RecordNotFoundException:
        log.error(
            f"Zendesk user {zd_ticket.requester_id} for chat ticket {zd_ticket.id} doesn't exist."
        )
        return None

    if not zd_user.external_id:
        log.error(
            f"Zendesk user {zd_ticket.requester_id} for chat ticket {zd_ticket.id} has no external_id."
        )
        return None

    user = User.objects.filter(profile__fxa_uid=zd_user.external_id).first()

    if user is None:
        log.error(f"No SUMO user for the requester of chat ticket {zd_ticket.id}.")
        return None

    return create_support_ticket(user, product, zd_ticket=zd_ticket)


def system_tags(tags) -> list[str]:
    return [tag for tag in tags if tag in ("loginless_ticket", "stage") or tag.startswith("seg-")]


def generate_classification_tags(submission: SupportTicket, result: dict[str, Any]) -> list[str]:
    """
    Generate Zendesk tags from LLM classification results.

    Returns tier tags (t1-, t2-, t3-), legacy tags, and automation tags based on the classified topic.
    If product was reassigned, includes "other" tag.
    """
    product_slug = submission.product.slug
    topic_result = result.get("topic_result", {})
    product_result = result.get("product_result", {})

    tags = []

    # If product reassignment, add "other" tag
    if product_result.get("product"):
        tags.append("other")

    # Get topic title from classification
    topic_title = topic_result.get("topic", "")

    # Find topic in database and build tier tags
    topic = Topic.objects.filter(
        title=topic_title, products__slug=product_slug, is_archived=False
    ).first()

    # If no topic or "Undefined" or topic not found in DB
    # return current tags and legacy tag "general"
    if not topic_title or topic_title == "Undefined" or not topic:
        return ["undefined", "general", *tags]

    tags.extend(topic.tier_tags)
    try:
        tags.extend(submission.context["automation_tags"].get(str(topic.pk), []))
    except MissingTicketContext:
        pass

    # Legacy bucket lives on the t1 root Topic; fall back to "general" if unset.
    root = topic
    while root.parent_id is not None:
        root = root.parent
    tags.append(root.legacy_tag or "general")

    return tags


def send_support_ticket_to_zendesk(submission: SupportTicket) -> bool:
    """Send a support ticket to Zendesk. Returns True if successful."""

    def _handle_zendesk_exception(error: Exception) -> bool:
        """Flag a support ticket for manual review when Zendesk submission fails."""
        submission.submission_status = SupportTicket.STATUS_FLAGGED
        submission.save(update_fields=["submission_status"])
        flag_object(
            submission,
            by_user=Profile.get_sumo_bot(),
            notes=f"Failed to send to Zendesk: {error!s}",
            status=FlaggedObject.FLAG_PENDING,
            reason=FlaggedObject.REASON_OTHER,
        )
        return False

    try:
        context = submission.context
        ticket_fields = {
            "subject": submission.subject,
            "description": submission.description,
            "category": submission.category,
            "email": submission.email,
            "os": submission.os,
            "country": submission.country,
            "update_channel": submission.update_channel,
            "policy_distribution": submission.policy_distribution,
            "urgency": submission.urgency,
            "product": context["product_value"],
            "product_title": submission.product.title,
            "zendesk_tags": submission.zendesk_tags,
            "ticket_form_id": int(context["form_id"]),
            "brand_id": int(context["brand_id"]) if context["brand_id"] else None,
            "origin": submission.origin,
        }
        if submission.origin == SupportTicket.Origin.ENTERPRISE:
            organization_id = (
                ZendeskOrganization.objects.filter(
                    external_id=context.get("company", {}).get("external_id"),
                    group_profile_id=submission.org_group_id,
                )
                .values_list("zendesk_id", flat=True)
                .first()
            )
            if not organization_id:
                raise TicketHeld("The company has no linked Zendesk organization")
            if (
                not submission.user
                or not submission.user.is_active
                or list(
                    GroupProfile.objects.enterprise_companies(submission.user).values_list(
                        "pk", flat=True
                    )[:2]
                )
                != [submission.org_group_id]
            ):
                raise TicketHeld("The requester is no longer a member of the accepted company")
            # Only membership synchronization may create enterprise requesters in Zendesk.
            if not submission.user.profile.zendesk_id:
                raise TicketHeld(
                    "The requester has not been provisioned in the company's Zendesk organization"
                )
            ticket_fields["organization_id"] = organization_id
        ticket_audit = ZendeskClient().create_ticket(submission.user, ticket_fields)
        submission.zendesk_ticket_id = str(ticket_audit.ticket.id)
        submission.submission_status = SupportTicket.STATUS_SENT
        submission.save(update_fields=["zendesk_ticket_id", "submission_status"])
        return True
    except APIException as e:
        error_str = str(e)
        if "UserSuspended" in error_str or "RecordInvalid" in error_str:
            if submission.origin == SupportTicket.Origin.ENTERPRISE:
                error_class = "UserSuspended" if "UserSuspended" in error_str else "RecordInvalid"
                return _handle_zendesk_exception(
                    TicketHeld(f"Zendesk refused the ticket ({error_class})")
                )
            submission.submission_status = SupportTicket.STATUS_REJECTED
            submission.save(update_fields=["submission_status"])
            return False
        return _handle_zendesk_exception(e)
    except Exception as e:
        return _handle_zendesk_exception(e)


def process_zendesk_classification_result(
    submission: SupportTicket,
    result: dict[str, Any],
) -> None:
    """
    Process the classification result from the LLM and take moderation action.
    Handles spam, flag review, and sends to Zendesk if not spam.

    The waffle switch controls whether flagged items go to moderation queue:
    - Active: Create FlaggedObject for moderation queue (manual review)
    - Inactive: Fully automated - reject spam without creating FlaggedObject
    """
    sumo_bot = Profile.get_sumo_bot()

    def flag_submission(
        notes: str,
        status: int = FlaggedObject.FLAG_PENDING,
        reason: str = FlaggedObject.REASON_CONTENT_MODERATION,
        submission_status: str = SupportTicket.STATUS_FLAGGED,
    ) -> None:
        """Helper function to update submission status and create a flag."""
        submission.submission_status = submission_status
        submission.save(update_fields=["submission_status"])
        flag_object(
            submission,
            by_user=sumo_bot,
            notes=notes,
            status=status,
            reason=reason,
        )

    action = result.get("action")

    match action:
        case ModerationAction.SPAM:
            notes = (
                f"LLM classified as spam, for the following reason:\n"
                f"{result.get('spam_result', {}).get('reason', '')}"
            )

            if waffle.switch_is_active("zendesk-spam-classifier"):
                flag_submission(
                    notes=notes,
                    status=FlaggedObject.FLAG_PENDING,
                    reason=FlaggedObject.REASON_SPAM,
                )
            else:
                submission.submission_status = SupportTicket.STATUS_REJECTED
                submission.save(update_fields=["submission_status"])
        case ModerationAction.FLAG_REVIEW:
            notes = (
                f"LLM flagged for manual review, for the following reason:\n"
                f"{result.get('spam_result', {}).get('reason', '')}"
            )
            flag_submission(
                notes=notes,
                status=FlaggedObject.FLAG_PENDING,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
            )
        case ModerationAction.NOT_SPAM:
            # Find and set topic if classified
            topic_title = result.get("topic_result", {}).get("topic")
            if topic_title and topic_title != "Undefined":
                topic = Topic.objects.filter(
                    title=topic_title, products=submission.product, is_archived=False
                ).first()
                if topic:
                    submission.topic = topic

            # Generate classification tags
            classification_tags = generate_classification_tags(submission, result)

            # Replace with system tags + classification tags
            submission.zendesk_tags = system_tags(submission.zendesk_tags) + classification_tags
            submission.save(update_fields=["zendesk_tags", "topic"])

            send_support_ticket_to_zendesk(submission)
        case _:
            flag_submission(
                notes=f"Unknown classification action: {action}",
                status=FlaggedObject.FLAG_PENDING,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
            )
