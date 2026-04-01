import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.dateparse import parse_datetime

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


@shared_task
@skip_if_read_only_mode
def process_zendesk_update(payload: dict) -> None:
    """Process an incoming Zendesk webhook payload.

    Updates the matching SupportTicket with status, comments, and tags
    from the payload. Handles partial payloads gracefully — only fields
    present in the payload are updated.
    """
    if not (ticket_id := payload.get("ticket_id")):
        log.warning("Zendesk webhook payload missing ticket_id.")
        return

    try:
        ticket = SupportTicket.objects.get(zendesk_ticket_id=str(ticket_id))
    except SupportTicket.DoesNotExist:
        return

    update_fields = []

    if "updated_at" in payload:
        ticket.zd_updated_at = parse_datetime(payload["updated_at"])
        update_fields.append("zd_updated_at")

    if "status" in payload:
        ticket.zd_status = payload["status"]
        update_fields.append("zd_status")

    if "tags" in payload:
        internal_zd_tags = payload["tags"]
        if not isinstance(internal_zd_tags, list):
            raise ValueError("Unexpected tags structure from Zendesk")
        ticket.internal_zd_tags = internal_zd_tags
        update_fields.append("internal_zd_tags")

    if "latest_comment" in payload:
        latest_comment = payload["latest_comment"]
        if not isinstance(latest_comment, dict):
            raise ValueError("Unexpected comment structure from Zendesk")
        latest_comment["created_at"] = payload.get("updated_at")
        ticket.comments.append(latest_comment)
        update_fields.append("comments")

    if update_fields:
        update_fields.append("last_synced_at")
        ticket.last_synced_at = timezone.now()
        ticket.save(update_fields=update_fields)
