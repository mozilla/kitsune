import re
from typing import Any, cast

import waffle

from kitsune.customercare import ZENDESK_CATEGORIES, ZENDESK_LEGACY_MAPPING
from kitsune.customercare.forms import ZENDESK_PRODUCT_SLUGS
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.products.models import Topic
from kitsune.questions.utils import flag_object
from kitsune.users.models import Profile


def _topic_to_tag(text: str) -> str:
    """Convert topic title to tag format: lowercase, remove punctuation, spaces to dashes."""
    tag = text.lower()
    tag = re.sub(r"[,.]", "", tag)
    tag = re.sub(r"\s+", "-", tag)
    return tag


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
    topic_title = topic_result.get("topic")

    # If no topic or "Undefined", return current tags
    if not topic_title:
        return ["undefined", *tags]

    if topic_title == "Undefined":
        return tags

    # Find topic in database and build tier tags
    try:
        topic = Topic.objects.filter(
            title=topic_title, products__slug=product_slug, is_archived=False
        ).first()

        if not topic:
            return ["undefined", *tags]

        # Build path from topic to root
        path = [topic]
        current = topic
        while current.parent:
            current = current.parent
            path.insert(0, current)

        # Convert to tier tags
        tier_tags = []
        for i, t in enumerate(path, start=1):
            tier_tags.append(f"t{i}-{_topic_to_tag(t.title)}")

        tags.extend(tier_tags)

        # Find matching automation tags
        categories = cast(list, ZENDESK_CATEGORIES.get(product_slug, []))
        for category in categories:
            category_tiers = category.get("tags", {}).get("tiers", [])
            if set(tier_tags) == set(category_tiers):
                automation = category.get("tags", {}).get("automation")
                if automation:
                    tags.append(automation)
                break

        # Find matching legacy tag or fallback to "general" legacy tag.
        for legacy_tag, topic_tags in ZENDESK_LEGACY_MAPPING.items():
            if set(tier_tags) & topic_tags:
                tags.append(legacy_tag)
                break
        else:
            tags.append("general")

    except Exception:
        return ["undefined", *tags]

    return tags


def send_support_ticket_to_zendesk(submission: SupportTicket) -> bool:
    """Send a support ticket to Zendesk. Returns True if successful."""

    zendesk_product = (
        ZENDESK_PRODUCT_SLUGS.get(submission.product.slug, submission.product.slug)
        if submission.product.slug == "mozilla-vpn"
        else submission.product.slug
    )

    client = ZendeskClient()
    ticket_fields = {
        "subject": submission.subject,
        "description": submission.description,
        "category": submission.category,
        "email": submission.email,
        "os": submission.os,
        "country": submission.country,
        "product": zendesk_product,
        "product_title": submission.product.title,
        "zendesk_tags": submission.zendesk_tags,
    }

    try:
        ticket_audit = client.create_ticket(submission.user, ticket_fields)
        submission.zendesk_ticket_id = str(ticket_audit.ticket.id)
        submission.status = SupportTicket.STATUS_SENT
        submission.save(update_fields=["zendesk_ticket_id", "status"])
        return True
    except Exception as e:
        # If sending fails, flag for review
        submission.status = SupportTicket.STATUS_FLAGGED
        submission.save(update_fields=["status"])
        flag_object(
            submission,
            by_user=Profile.get_sumo_bot(),
            notes=f"Failed to send to Zendesk: {e!s}",
            status=FlaggedObject.FLAG_PENDING,
            reason=FlaggedObject.REASON_OTHER,
        )
        return False


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
        submission.status = submission_status
        submission.save(update_fields=["status"])
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
                submission.status = SupportTicket.STATUS_REJECTED
                submission.save(update_fields=["status"])
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
                tag for tag in submission.zendesk_tags if tag in ["loginless_ticket", "stage"]
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
