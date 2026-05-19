import logging
from contextlib import contextmanager
from datetime import timedelta

import requests
from celery import group, shared_task
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from zenpy.lib.exception import APIException

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.utils import (
    is_permanent_zendesk_error,
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
def post_reply_to_zendesk(ticket_id: int) -> None:
    """Post the ticket's pending comment to Zendesk and clear it on success.

    Single try, no auto-retry. The user retries via the reply form (same body =
    re-attempt, different body = replace).

    On any exception, mark the pending as failed and re-raise unless it's a
    transient APIException/RequestException — permanent and unknown exceptions
    propagate to Celery so Sentry captures them.
    """
    try:
        with _locked_ticket(ticket_id, select_related=["user"]) as ticket:
            if not (user := ticket.user):
                # Orphan ticket — no user to display the failure to. Clear the
                # pending so we don't leave dead state behind.
                if ticket.pending_changes.pop("comment", None) is not None:
                    ticket.save(update_fields=["pending_changes"])
                return

            pending = ticket.pending_changes.get("comment")
            if not pending or pending.get("status") != "sending":
                return

            author_zd_id = int(user.profile.zendesk_id) if user.profile.zendesk_id else None
            body = pending["body"]

            # Record the attempt time so the stale-flip can fire if we get stuck.
            pending["last_attempted_at"] = timezone.now().isoformat()
            ticket.save(update_fields=["pending_changes"])

        ticket_audit = ZendeskClient().add_ticket_comment(
            user=user,
            ticket_id=int(ticket.zendesk_ticket_id),
            comment_body=body,
            public=True,
        )

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
                f"Zendesk audit had no comment event for ticket {ticket.zendesk_ticket_id}"
            )

        # Append the actual comment and clear the pending comment if it still matches
        # what we posted. If the user has replaced the pending comment mid-flight
        # (different body), we leave their new pending comment alone.
        with _locked_ticket(ticket_id) as ticket:
            new_id = new_comment["id"]
            fields = []
            if not any(c.get("id") == new_id for c in ticket.comments):
                ticket.comments.append(
                    {
                        "id": new_id,
                        "body": new_comment.get("body", ""),
                        "created_at": ticket_audit.ticket.updated_at,
                        "public": True,
                        "author": {
                            "name": user.profile.display_name,
                            "id": author_zd_id,
                        },
                    }
                )
                fields.append("comments")
            pending = ticket.pending_changes.get("comment", {})
            if pending.get("body") == body:
                ticket.pending_changes.pop("comment", None)
                fields.append("pending_changes")
            if fields:
                ticket.save(update_fields=fields)
    except SupportTicket.DoesNotExist:
        return
    except Exception as exc:
        log.exception(f"Failed to post reply for ticket id {ticket_id}")
        allow_retries = isinstance(
            exc, APIException | requests.exceptions.RequestException
        ) and not is_permanent_zendesk_error(exc)
        _mark_pending_failed(ticket_id, allow_retries=allow_retries)
        if allow_retries:
            return
        raise


@contextmanager
def _locked_ticket(ticket_id, select_related=None):
    """Open a transaction and yield the SupportTicket under a row lock.

    Pass an iterable of field names as `select_related` to add `select_related()`
    (e.g. `["user"]`); when provided, the lock is scoped to `of=("self",)` so
    the joined rows aren't locked too. Used to bracket read-modify-write
    sequences on pending_changes and comments. The lock is held until the
    transaction exits.
    """
    with transaction.atomic():
        if select_related:
            qs = SupportTicket.objects.select_for_update(of=("self",)).select_related(
                *select_related
            )
        else:
            qs = SupportTicket.objects.select_for_update()
        yield qs.get(id=ticket_id)


def _mark_pending_failed(ticket_id, allow_retries):
    """Mark the pending comment as failed under a row lock.

    No-op if there's no pending comment or its status is no longer "sending"
    (e.g., user replaced it while we were running).
    """
    with _locked_ticket(ticket_id) as ticket:
        pending = ticket.pending_changes.get("comment", {})
        if pending.get("status") != "sending":
            return
        pending["status"] = "failed"
        pending["allow_retries"] = allow_retries
        ticket.save(update_fields=["pending_changes"])


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
            # Skip if the incoming comment "id" is already present.
            if (comment_id := comment.get("id")) and not any(
                c.get("id") == comment_id for c in ticket.comments
            ):
                comment["created_at"] = updated_at
                comment["public"] = comment.pop("is_public", False)
                ticket.comments.append(comment)
                update_fields.append("comments")

        if update_fields:
            ticket.zd_updated_at = parse_datetime(updated_at)
            update_fields.append("zd_updated_at")
            ticket.save(update_fields=update_fields)


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
        SupportTicket.ZD_STATUS_OPEN,
        SupportTicket.ZD_STATUS_PENDING,
        SupportTicket.ZD_STATUS_WAITING,
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
