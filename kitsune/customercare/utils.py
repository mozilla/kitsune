from typing import Any

import waffle

from kitsune.customercare.forms import ZENDESK_PRODUCT_SLUGS
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.questions.utils import flag_object
from kitsune.users.models import Profile


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
        ticket = client.create_ticket(submission.user, ticket_fields)
        submission.zendesk_ticket_id = str(ticket.id)
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
            send_support_ticket_to_zendesk(submission)
        case _:
            flag_submission(
                notes=f"Unknown classification action: {action}",
                status=FlaggedObject.FLAG_PENDING,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
            )
