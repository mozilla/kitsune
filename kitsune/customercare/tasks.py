import logging
from datetime import timedelta

import requests
from celery import shared_task
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from zenpy.lib.api_objects import Comment
from zenpy.lib.exception import APIException

from kitsune.customercare.models import SupportTicket, SupportTicketReplyOutbox
from kitsune.customercare.utils import process_zendesk_classification_result
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.llm.support.classifiers import classify_zendesk_submission
from kitsune.sumo.decorators import skip_if_read_only_mode

log = logging.getLogger("k.task")

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)

SIMPLE_FIELD_EVENT_MAP = {
    "zen:event-type:ticket.status_changed": "zd_status",
    "zen:event-type:ticket.subject_changed": "subject",
    "zen:event-type:ticket.description_changed": "description",
}
COMMENT_ADDED_EVENT = "zen:event-type:ticket.comment_added"
HANDLED_EVENT_TYPES = {COMMENT_ADDED_EVENT, *SIMPLE_FIELD_EVENT_MAP}


@shared_task_with_retry
def zendesk_submission_classifier(submission_id: int) -> None:
    """Classify a support ticket for spam and process the result.

    Always runs the classifier. The waffle switch only controls
    behavior when spam is detected (flag for moderation vs reject).

    If classification fails after all retries, marks ticket as
    STATUS_PROCESSING_FAILED for periodic task to handle.
    """
    try:
        submission = SupportTicket.objects.get(id=submission_id)
    except SupportTicket.DoesNotExist:
        return

    try:
        result = classify_zendesk_submission(submission)
        process_zendesk_classification_result(submission, result)
    except Exception as e:
        # After all retries exhausted, mark as processing failed
        log.error(f"Classification failed for ticket {submission_id}: {e}", exc_info=True)
        submission.submission_status = SupportTicket.STATUS_PROCESSING_FAILED
        submission.save(update_fields=["submission_status"])
        raise


@shared_task
def update_zendesk_user(user_id: int) -> None:
    user = User.objects.get(pk=user_id)
    if user.profile.zendesk_id:
        zendesk = ZendeskClient()
        zendesk.update_user(user)


@shared_task
def update_zendesk_identity(user_id: int, email: str) -> None:
    user = User.objects.get(pk=user_id)
    zendesk_user_id = user.profile.zendesk_id

    # fetch identity id
    if zendesk_user_id:
        zendesk = ZendeskClient()
        zendesk.update_primary_email(zendesk_user_id, email)


@shared_task
@skip_if_read_only_mode
def auto_reject_old_zendesk_spam() -> None:
    """Auto-reject Zendesk spam tickets older than 14 days."""
    cutoff_date = timezone.now() - timedelta(days=14)
    ct_support_ticket = ContentType.objects.get_for_model(SupportTicket)

    old_spam_flags = FlaggedObject.objects.filter(
        reason=FlaggedObject.REASON_SPAM,
        content_type=ct_support_ticket,
        status=FlaggedObject.FLAG_PENDING,
        created__lt=cutoff_date,
    ).prefetch_related("content_object")

    rejected_count = 0

    for flag in old_spam_flags:
        if (
            flag.content_object
            and flag.content_object.submission_status == SupportTicket.STATUS_FLAGGED
        ):
            flag.content_object.submission_status = SupportTicket.STATUS_REJECTED
            flag.content_object.save(update_fields=["submission_status"])
            rejected_count += 1

        flag.status = FlaggedObject.FLAG_ACCEPTED
        flag.save(update_fields=["status"])

    log.info(
        f"Auto-rejected {rejected_count} old Zendesk spam tickets older than {cutoff_date.date()}"
    )


@shared_task
@skip_if_read_only_mode
def process_failed_zendesk_tickets() -> None:
    """Send tickets to Zendesk where classification/processing failed.

    This is a safety net for cases where classification fails after all retries.
    Sends the ticket to Zendesk with whatever tags are currently set.
    """
    from kitsune.customercare.utils import send_support_ticket_to_zendesk

    failed_tickets = SupportTicket.objects.filter(
        submission_status=SupportTicket.STATUS_PROCESSING_FAILED
    )

    processed_count = 0

    for ticket in failed_tickets:
        # Send to Zendesk with whatever tags are currently set
        success = send_support_ticket_to_zendesk(ticket)
        if success:
            processed_count += 1

    if processed_count > 0:
        log.info(f"Processed {processed_count} failed Zendesk tickets")


@shared_task
@skip_if_read_only_mode
def process_zendesk_update(payload: dict) -> None:
    """
    Process an incoming Zendesk ticket-event webhook payload. The Zendesk
    Webhook must be created based on Zendesk events rather than triggers
    or automation.

    Handles these event types:
      - ticket.comment_added
      - ticket.status_changed
      - ticket.subject_changed
      - ticket.description_changed
    """
    if (event_type := payload.get("type")) not in HANDLED_EVENT_TYPES:
        if event_type:
            log.warning(f"Unhandled event type: {event_type}.")
        return

    if not (
        (detail := payload.get("detail"))
        and (ticket_id := detail.get("id"))
        and (updated_at := detail.get("updated_at"))
    ):
        raise ValueError("Zendesk webhook payload missing detail.id or detail.updated_at.")

    if not (event := payload.get("event")):
        raise ValueError("Zendesk webhook payload missing event information.")

    with transaction.atomic():
        try:
            ticket = SupportTicket.objects.select_for_update().get(
                zendesk_ticket_id=str(ticket_id)
            )
        except SupportTicket.DoesNotExist:
            return

        update_fields = []

        if field := SIMPLE_FIELD_EVENT_MAP.get(event_type):
            setattr(ticket, field, event.get("current"))
            update_fields.append(field)
        elif event_type == COMMENT_ADDED_EVENT:
            comment = event.get("comment")
            if not isinstance(comment, dict):
                raise ValueError("Unexpected comment structure from Zendesk")
            comment["created_at"] = updated_at
            comment["public"] = comment.pop("is_public", False)
            ticket.comments.append(comment)
            update_fields.append("comments")
            # The mirror now carries this comment id — drop the matching outbox row
            # so it doesn't double-render alongside the mirrored copy.
            if comment_id := comment.get("id"):
                SupportTicketReplyOutbox.objects.filter(
                    ticket=ticket,
                    status=SupportTicketReplyOutbox.STATUS_POSTED,
                    zendesk_comment_id=comment_id,
                ).delete()

        if update_fields:
            ticket.zd_updated_at = parse_datetime(updated_at)
            update_fields.append("zd_updated_at")
            ticket.save(update_fields=update_fields)


PERMANENT_HTTP_CODES = {400, 401, 403, 404, 422}
MAX_OUTBOX_ATTEMPTS = 3


def _is_permanent(exc):
    """Classify a Zendesk-side exception as terminal vs worth retrying."""
    if isinstance(exc, ValueError):
        return True
    if isinstance(exc, APIException):
        code = getattr(getattr(exc, "response", None), "status_code", None)
        return code in PERMANENT_HTTP_CODES
    # requests transport errors (ConnectionError, Timeout, ...) → transient
    return False


def _extract_new_comment_id(audit):
    """Pull the new Zendesk comment id out of a TicketAudit's events list.

    `audit.events` is a list of typed objects; the one we created is a Comment
    instance with `.id`. We created exactly one — return its id or None.
    """
    return next(
        (
            ev.id
            for ev in (getattr(audit, "events", None) or [])
            if isinstance(ev, Comment) and getattr(ev, "id", None)
        ),
        None,
    )


@shared_task_with_retry
def post_outbox_reply(outbox_id: int) -> None:
    """Post a queued user reply to Zendesk.

    Idempotent: re-loads the row and short-circuits on terminal states.

    NOTE: there is a small window between Zendesk accepting the comment and our
    success UPDATE landing. If we crash inside it, the comment is on Zendesk's
    side but our row stays `pending`; a Celery retry would double-post. Accepted
    iteration-1 risk.
    """
    try:
        outbox = SupportTicketReplyOutbox.objects.select_related("ticket", "author").get(
            id=outbox_id
        )
    except SupportTicketReplyOutbox.DoesNotExist:
        return

    if outbox.status in (
        SupportTicketReplyOutbox.STATUS_POSTED,
        SupportTicketReplyOutbox.STATUS_FAILED,
    ):
        return

    if not (outbox.author and outbox.author.is_authenticated):
        outbox.status = SupportTicketReplyOutbox.STATUS_FAILED
        outbox.error_reason = "Author missing or anonymous."
        outbox.save(update_fields=["status", "error_reason", "updated_at"])
        return

    if not outbox.ticket.zendesk_ticket_id:
        outbox.status = SupportTicketReplyOutbox.STATUS_FAILED
        outbox.error_reason = "Ticket has no Zendesk id."
        outbox.save(update_fields=["status", "error_reason", "updated_at"])
        return

    try:
        audit = ZendeskClient().add_ticket_comment(
            user=outbox.author,
            ticket_id=outbox.ticket.zendesk_ticket_id,
            comment_body=outbox.body,
            public=True,
        )
    except (APIException, requests.exceptions.RequestException, ValueError) as exc:
        outbox.attempt_count = (outbox.attempt_count or 0) + 1
        if _is_permanent(exc) or outbox.attempt_count >= MAX_OUTBOX_ATTEMPTS:
            outbox.status = SupportTicketReplyOutbox.STATUS_FAILED
            outbox.error_reason = str(exc)[:500]
            outbox.save(update_fields=["status", "error_reason", "attempt_count", "updated_at"])
            return
        outbox.save(update_fields=["attempt_count", "updated_at"])
        raise  # transient → Celery autoretries

    new_comment_id = _extract_new_comment_id(audit)
    if new_comment_id is None:
        outbox.status = SupportTicketReplyOutbox.STATUS_FAILED
        outbox.error_reason = "Zendesk returned no comment id."
        outbox.attempt_count = (outbox.attempt_count or 0) + 1
        outbox.save(update_fields=["status", "error_reason", "attempt_count", "updated_at"])
        return

    outbox.zendesk_comment_id = new_comment_id
    outbox.posted_at = timezone.now()
    outbox.status = SupportTicketReplyOutbox.STATUS_POSTED
    outbox.save(update_fields=["status", "zendesk_comment_id", "posted_at", "updated_at"])
