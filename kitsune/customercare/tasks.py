import json
import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

# from django.db import transaction
from django.utils import timezone

# from django.utils.dateparse import parse_datetime
from kitsune.customercare.models import SupportTicket
from kitsune.customercare.utils import process_zendesk_classification_result
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.llm.support.classifiers import classify_zendesk_submission
from kitsune.sumo.decorators import skip_if_read_only_mode

log = logging.getLogger("k.task")

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)


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


SIMPLE_FIELD_EVENT_MAP = {
    "zen:event-type:ticket.status_changed": "zd_status",
    "zen:event-type:ticket.subject_changed": "subject",
    "zen:event-type:ticket.description_changed": "description",
}
COMMENT_ADDED_EVENT = "zen:event-type:ticket.comment_added"
HANDLED_EVENT_TYPES = {COMMENT_ADDED_EVENT, *SIMPLE_FIELD_EVENT_MAP}


@shared_task
@skip_if_read_only_mode
def process_zendesk_update(payload: dict) -> None:
    """Process an incoming Zendesk ticket-event webhook payload.

    Handles these event types:
      - ticket.comment_added
      - ticket.status_changed
      - ticket.subject_changed
      - ticket.description_changed
    """
    log.info("---- Zendesk Payload ----")
    log.info(json.dumps(payload, indent=2, default=str))
    log.info("-------------------------")

    event_type = payload.get("type")
    if event_type not in HANDLED_EVENT_TYPES:
        return

    detail = payload.get("detail") or {}
    ticket_id = detail.get("id")
    if not ticket_id:
        log.warning("Zendesk webhook payload missing detail.id.")
        return

    # event = payload.get("event") or {}

    # with transaction.atomic():
    #     try:
    #         ticket = SupportTicket.objects.select_for_update().get(
    #             zendesk_ticket_id=str(ticket_id)
    #         )
    #     except SupportTicket.DoesNotExist:
    #         return

    #     update_fields = []

    #     if field := SIMPLE_FIELD_EVENT_MAP.get(event_type):
    #         current_value = getattr(ticket, field)
    #         previous = event.get("previous")
    #         if current_value != previous:
    #             log.warning(
    #                 f"Skipping {event_type} for ticket {ticket_id}: "
    #                 f"current {field}={current_value!r} does not match "
    #                 f"event previous={previous!r}"
    #             )
    #             return
    #         setattr(ticket, field, event.get("current"))
    #         update_fields.append(field)
    #     elif event_type == COMMENT_ADDED_EVENT:
    #         comment = event.get("comment")
    #         if not isinstance(comment, dict):
    #             raise ValueError("Unexpected comment structure from Zendesk")
    #         ticket.comments.append({**comment, "created_at": payload.get("time")})
    #         update_fields.append("comments")

    #     if "updated_at" in detail:
    #         ticket.zd_updated_at = parse_datetime(detail["updated_at"])
    #         update_fields.append("zd_updated_at")

    #     if update_fields:
    #         update_fields.append("last_synced_at")
    #         ticket.last_synced_at = timezone.now()
    #         ticket.save(update_fields=update_fields)
