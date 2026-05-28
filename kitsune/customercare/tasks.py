import logging
from datetime import timedelta

from celery import group, shared_task
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from kitsune.customercare.models import SupportTicket, SupportTicketPendingChange
from kitsune.customercare.utils import (
    apply_zendesk_ticket_data,
    fetch_zendesk_ticket_data,
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

HANDLED_EVENT_TYPES = {
    "zen:event-type:ticket.status_changed",
    "zen:event-type:ticket.subject_changed",
    "zen:event-type:ticket.description_changed",
    "zen:event-type:ticket.comment_added",
}


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
def post_reply_to_zendesk(ticket_id: int) -> None:
    """Post the ticket's pending comment to Zendesk and clear it on success.

    Single try, no auto-retry. The user retries via the reply form, which is
    gated on STATUS_FAILED — while this task runs (STATUS_SENDING) the form
    refuses replacement, so the pending row is stable for the task's lifetime.

    Failure modes:
      - Before Zendesk confirms the comment: flip the pending to FAILED so the
        form re-enables retry.
      - After Zendesk confirms: the user has already succeeded. Don't flip.
        Try to mirror locally (next periodic sync reconciles if this fails),
        then always clear the pending so the user isn't stuck in "sending".
    """
    try:
        with transaction.atomic():
            try:
                pending = (
                    SupportTicketPendingChange.objects.filter(
                        ticket_id=ticket_id,
                        kind=SupportTicketPendingChange.KIND_COMMENT,
                        status=SupportTicketPendingChange.STATUS_SENDING,
                    )
                    .select_related("ticket", "ticket__user")
                    .select_for_update(of=("self",), skip_locked=True)
                    .get()
                )
            except SupportTicketPendingChange.DoesNotExist:
                return

            if not (user := pending.ticket.user):
                # Orphan ticket — no user to display the failure to. Clear the
                # pending so we don't leave dead state behind.
                pending.delete()
                return

            if pending.ticket.zd_status == SupportTicket.ZD_STATUS_CLOSED:
                # Ticket closed between view acceptance and task execution.
                # Zendesk rejects comments on closed tickets and the form is
                # hidden, so the user can't retry — drop the pending.
                pending.delete()
                return

            # Record the attempt time so the stale-flip can fire if we get stuck.
            pending.last_attempted_at = timezone.now()
            pending.save(update_fields=["last_attempted_at"])

        # Zendesk automatically triggers a reopen only when the comment author
        # is the same as the API user, which is never true in our case, so we
        # take care of that here.
        new_status = (
            SupportTicket.ZD_STATUS_OPEN
            if pending.ticket.zd_status
            in {SupportTicket.ZD_STATUS_PENDING, SupportTicket.ZD_STATUS_SOLVED}
            else None
        )
        ticket_audit = ZendeskClient().add_ticket_comment(
            user=user,
            ticket_id=int(pending.ticket.zendesk_ticket_id),
            comment_body=pending.payload,
            public=True,
            status=new_status,
        )
    except Exception:
        log.exception(f"Failed to post reply for ticket id {ticket_id}")
        SupportTicketPendingChange.objects.filter(
            ticket_id=ticket_id,
            kind=SupportTicketPendingChange.KIND_COMMENT,
            status=SupportTicketPendingChange.STATUS_SENDING,
        ).update(status=SupportTicketPendingChange.STATUS_FAILED)
        raise

    # Get the newly-added comment from the audit's events, append it to the ticket's
    # comments for now, and clear the pending comment. The webhook will take care of
    # fully syncing the support ticket with Zendesk later.
    try:
        new_comment = next(
            (
                ev
                for ev in ticket_audit.audit.events
                if isinstance(ev, dict) and ev.get("type") == "Comment" and ev.get("id")
            ),
            None,
        )
        if new_comment is None:
            raise ValueError(
                f"Zendesk audit had no comment event for ticket {ticket_audit.ticket.id}."
            )

        with transaction.atomic():
            try:
                ticket = SupportTicket.objects.select_for_update().get(id=ticket_id)
            except SupportTicket.DoesNotExist:
                return

            ticket.zd_status = ticket_audit.ticket.status
            ticket.zd_updated_at = parse_datetime(ticket_audit.ticket.updated_at)
            update_fields = ["zd_status", "zd_updated_at"]

            new_comment_id = new_comment["id"]
            if not any(c.get("id") == new_comment_id for c in ticket.comments):
                ticket.comments.append(
                    {
                        "id": new_comment_id,
                        "body": new_comment["html_body"],
                        "created_at": ticket_audit.ticket.updated_at,
                        "public": True,
                        "author": {
                            "name": user.profile.display_name,
                            "id": new_comment["author_id"],
                        },
                    }
                )
                update_fields.append("comments")

            ticket.save(update_fields=update_fields)
    finally:
        pending.delete()


@shared_task
@skip_if_read_only_mode
def process_zendesk_update(payload: dict) -> None:
    """
    Process an incoming Zendesk ticket-event webhook payload by re-syncing
    the affected ticket from Zendesk via the REST API. The webhook is a
    notification trigger only; the REST API is the source of truth.
    """
    if not (detail := payload.get("detail")) or not (ticket_id := detail.get("id")):
        raise ValueError("Zendesk webhook payload missing detail.id.")

    event_type = payload.get("type")
    if event_type not in HANDLED_EVENT_TYPES:
        log.warning(f"Unhandled Zendesk event type: {event_type or 'missing'}.")
        return

    qs = SupportTicket.objects.filter(zendesk_ticket_id=str(ticket_id))
    if not qs.exists():
        return

    zd_ticket, zd_comments = fetch_zendesk_ticket_data(str(ticket_id))

    with transaction.atomic():
        try:
            ticket = qs.select_for_update().get()
        except SupportTicket.DoesNotExist:
            return
        apply_zendesk_ticket_data(ticket, zd_ticket, zd_comments)


@shared_task_with_retry
def sync_support_ticket(ticket_id: int) -> None:
    """Refresh a single SupportTicket from Zendesk.

    Thin wrapper around `sync_ticket_from_zendesk`. Per-ticket task so a single
    failing ticket doesn't stall the rest of the batch and gets isolated retries.
    """
    try:
        ticket = (
            SupportTicket.objects.filter(zendesk_ticket_id__isnull=False)
            .exclude(zendesk_ticket_id="")
            .get(id=ticket_id)
        )
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
    active_statuses = [
        SupportTicket.ZD_STATUS_NEW,
        SupportTicket.ZD_STATUS_OPEN,
        SupportTicket.ZD_STATUS_PENDING,
        SupportTicket.ZD_STATUS_HOLD,
    ]
    ticket_ids = (
        SupportTicket.objects.filter(
            zd_status__in=active_statuses,
            zendesk_ticket_id__isnull=False,
        )
        .exclude(zendesk_ticket_id="")
        .values_list("id", flat=True)
    )

    result = group(sync_support_ticket.s(ticket_id) for ticket_id in ticket_ids).delay()

    log.info(f"Dispatched Zendesk sync for {len(result)} active tickets.")
