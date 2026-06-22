import logging
from datetime import timedelta

from celery import group, shared_task
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.utils import (
    process_zendesk_classification_result,
    sync_ticket_from_zendesk,
)
from kitsune.customercare.zendesk import ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.llm.support.classifiers import classify_zendesk_submission
from kitsune.sumo.decorators import skip_if_read_only_mode

log = logging.getLogger("k.task")

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)

# Zendesk webhook events that trigger a re-sync of the ticket from the Zendesk REST API.
RESYNC_EVENT_TYPES = {
    "zen:event-type:ticket.status_changed",
    "zen:event-type:ticket.subject_changed",
    "zen:event-type:ticket.description_changed",
    "zen:event-type:ticket.comment_added",
}
# Zendesk webhook events that only update the local deletion state of the support ticket.
UNDELETE_EVENT_TYPE = "zen:event-type:ticket.undeleted"
DELETION_EVENT_TYPES = {
    "zen:event-type:ticket.soft_deleted",
    "zen:event-type:ticket.permanently_deleted",
    UNDELETE_EVENT_TYPE,
}

HANDLED_EVENT_TYPES = RESYNC_EVENT_TYPES | DELETION_EVENT_TYPES


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
    Process an incoming Zendesk ticket-event webhook payload.

    Most events re-sync the affected ticket from Zendesk via the REST API. The
    webhook is only a notification trigger. The REST API is the source of truth.
    Deletion events are the exception. A deleted ticket no longer exists in Zendesk,
    so they only update the "zd_deleted_at" value and never touch the API.
    """
    if not (detail := payload.get("detail")) or not (ticket_id := detail.get("id")):
        raise ValueError("Zendesk webhook payload missing detail.id.")

    event_type = payload.get("type")
    if event_type not in HANDLED_EVENT_TYPES:
        log.warning(f"Unhandled Zendesk event type: {event_type or 'missing'}.")
        return

    qs = SupportTicket.objects.filter(zendesk_ticket_id=str(ticket_id))

    if event_type in DELETION_EVENT_TYPES:
        zd_deleted_at = (
            None
            if event_type == UNDELETE_EVENT_TYPE
            else parse_datetime(payload.get("time") or "") or timezone.now()
        )

        with transaction.atomic():
            try:
                ticket = qs.select_for_update().get()
            except SupportTicket.DoesNotExist:
                return

            ticket.zd_deleted_at = zd_deleted_at
            ticket.save(update_fields=["zd_deleted_at"])

        return

    try:
        ticket = qs.syncable().get()
    except SupportTicket.DoesNotExist:
        return

    sync_ticket_from_zendesk(ticket)


@shared_task_with_retry
def sync_support_ticket(ticket_id: int) -> None:
    """Refresh a single SupportTicket from Zendesk.

    Thin wrapper around `sync_ticket_from_zendesk`. Per-ticket task so a single
    failing ticket doesn't stall the rest of the batch and gets isolated retries.
    """
    try:
        ticket = SupportTicket.objects.syncable().get(id=ticket_id)
    except SupportTicket.DoesNotExist:
        return

    sync_ticket_from_zendesk(ticket)


@shared_task
@skip_if_read_only_mode
def sync_active_support_tickets() -> None:
    """Dispatch sync sub-tasks for all locally-active Zendesk tickets.

    Backup reconciliation path; the Zendesk webhook is the primary mechanism.
    Zenpy handles Zendesk API rate limiting, so sub-tasks run as fast as the
    worker pool allows.
    """
    ticket_ids = SupportTicket.objects.active().syncable().values_list("id", flat=True)

    result = group(sync_support_ticket.s(ticket_id) for ticket_id in ticket_ids).delay()

    log.info(f"Dispatched Zendesk sync for {len(result)} active tickets.")
