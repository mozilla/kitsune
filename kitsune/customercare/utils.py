from typing import Any

import waffle
from django.db import transaction
from django.utils import timezone
from zenpy.lib.exception import APIException, RecordNotFoundException

from kitsune.customercare.forms import ZENDESK_PRODUCT_SLUGS
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.groups.models import GroupProfile
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.products.models import Product, ProductSupportConfig, Topic, ZendeskTopic
from kitsune.questions.utils import flag_object
from kitsune.users.models import Profile


def _nearest_ancestor_org(user, candidates) -> GroupProfile | None:
    if not (user and user.is_authenticated):
        return None
    user_paths = list(GroupProfile.objects.filter(group__user=user).values_list("path", flat=True))
    matches = [cp for cp in candidates if any(p.startswith(cp.path) for p in user_paths)]
    if not matches:
        return None
    return max(matches, key=lambda cp: len(cp.path))


def resolve_org_group(submitter, product: Product) -> GroupProfile | None:
    config = ProductSupportConfig.objects.filter(
        product=product, is_active=True, zendesk_config__isnull=False
    ).first()
    if not (config and config.hybrid_support_groups.exists()):
        return None
    candidates = list(GroupProfile.objects.filter(group__in=config.hybrid_support_groups.all()))
    return _nearest_ancestor_org(submitter, candidates)


def resolve_user_org_group(user) -> GroupProfile | None:
    return _nearest_ancestor_org(user, list(GroupProfile.objects.org_roots()))


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
    ticket.subject = zd_ticket.subject
    ticket.description = zd_ticket.description
    ticket.comments = [
        {
            "id": c.id,
            "body": c.html_body,
            "created_at": c.created_at,
            "public": c.public,
            "author": {"name": c.author.name, "id": c.author.id},
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
    if ticket.is_zendesk_deleted:
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

    try:
        tags.extend(topic.tier_tags)

        # Automation tags from the ZendeskTopic linked to this Topic for this product.
        zd_topic = ZendeskTopic.objects.filter(
            topic=topic,
            configurations__zendesk_config__support_configs__product=submission.product,
            configurations__zendesk_config__support_configs__is_active=True,
        ).first()
        if zd_topic:
            tags.extend(zd_topic.automation_tags)

        # Legacy bucket lives on the t1 root Topic; fall back to "general" if unset.
        root = topic
        while root.parent_id is not None:
            root = root.parent
        tags.append(root.legacy_tag or "general")

    except Exception:
        return ["undefined", *tags]

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

    zendesk_product = (
        ZENDESK_PRODUCT_SLUGS.get(submission.product.slug, submission.product.slug)
        if submission.product.slug == "mozilla-vpn"
        else submission.product.slug
    )

    support_config = ProductSupportConfig.objects.get(product=submission.product, is_active=True)
    zendesk_config = support_config.zendesk_config
    ticket_form_id = zendesk_config.ticket_form_id

    client = ZendeskClient()
    ticket_fields = {
        "subject": submission.subject,
        "description": submission.description,
        "category": submission.category,
        "email": submission.email,
        "os": submission.os,
        "country": submission.country,
        "update_channel": submission.update_channel,
        "policy_distribution": submission.policy_distribution,
        "product": zendesk_product,
        "product_title": submission.product.title,
        "zendesk_tags": submission.zendesk_tags,
        "ticket_form_id": int(ticket_form_id),
        "brand_id": zendesk_config.brand_id,
    }

    try:
        ticket_audit = client.create_ticket(submission.user, ticket_fields)
        submission.zendesk_ticket_id = str(ticket_audit.ticket.id)
        submission.submission_status = SupportTicket.STATUS_SENT
        submission.save(update_fields=["zendesk_ticket_id", "submission_status"])
        return True
    except APIException as e:
        error_str = str(e)
        if "UserSuspended" in error_str or "RecordInvalid" in error_str:
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

            # Preserve system tags
            system_tags = [
                tag
                for tag in submission.zendesk_tags
                if tag in ["loginless_ticket", "stage"] or tag.startswith("seg-")
            ]

            # Generate classification tags
            classification_tags = generate_classification_tags(submission, result)

            # Replace with system tags + classification tags
            submission.zendesk_tags = system_tags + classification_tags
            submission.save(update_fields=["zendesk_tags", "topic"])

            send_support_ticket_to_zendesk(submission)
        case _:
            flag_submission(
                notes=f"Unknown classification action: {action}",
                status=FlaggedObject.FLAG_PENDING,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
            )
