import logging
from collections import defaultdict
from datetime import timedelta

import requests
import waffle
from celery import group, shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from zenpy.lib.exception import APIException, RecordNotFoundException, ZenpyException

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.utils import (
    adopt_chat_ticket,
    process_zendesk_classification_result,
    sync_ticket_from_zendesk,
)
from kitsune.customercare.zendesk import CHAT_REVOKED_TAG, ZendeskClient
from kitsune.flagit.models import FlaggedObject
from kitsune.groups.models import GroupProfile
from kitsune.llm.support.classifiers import classify_zendesk_submission
from kitsune.products.models import SupportContract, SupportCoverage
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.users.models import Profile

log = logging.getLogger("k.task")

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)

# Days the daily expiry cleanup looks back, so skipped runs still catch up.
CHAT_EXPIRY_WINDOW_DAYS = 7

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
# Zendesk webhook event that allows SUMO to collect tickets created via messaging.
CREATED_EVENT_TYPE = "zen:event-type:ticket.created"

HANDLED_EVENT_TYPES = RESYNC_EVENT_TYPES | DELETION_EVENT_TYPES | {CREATED_EVENT_TYPE}


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
    user = User.objects.select_related("profile").get(pk=user_id)
    profile = user.profile
    if not profile.zendesk_id:
        return
    if profile.is_unclaimed_invitee:
        # Ordinary sync would mark an unclaimed identity verified and replace its name.
        return
    ZendeskClient().update_user(user)


@shared_task_with_retry
def create_zendesk_user(user_id: int) -> None:
    """Give the user a Zendesk user, so later changes to their account reach Zendesk."""
    user = User.objects.filter(pk=user_id).select_related("profile").first()
    if user and not user.profile.zendesk_id and not user.profile.is_unclaimed_invitee:
        ZendeskClient().create_user(user)


@shared_task
def update_zendesk_identity(user_id: int, email: str) -> None:
    user = User.objects.get(pk=user_id)
    zendesk_user_id = user.profile.zendesk_id

    # fetch identity id
    if zendesk_user_id:
        zendesk = ZendeskClient()
        zendesk.update_primary_email(zendesk_user_id, email)


@shared_task
def tag_revoked_chat_tickets(zendesk_id: str, *, product_slugs=None, before=None) -> None:
    """Tag a user's active live-chat tickets once the user has lost chat access.

    Takes the Zendesk user id rather than the user, because once a user is deleted
    we can no longer look up their Zendesk user id.
    """
    # Turning chat off for everyone doesn't call for tagging anyone's tickets.
    if not waffle.switch_is_active("zendesk-chat"):
        return

    cutoff = parse_datetime(before) if before else timezone.now()
    prefix = settings.ZENDESK_CHAT_PRODUCT_TAG_PREFIX
    client = ZendeskClient()
    for ticket in client.get_active_chat_tickets(zendesk_id):
        if parse_datetime(ticket.created_at) > cutoff or CHAT_REVOKED_TAG in ticket.tags:
            continue
        if product_slugs is not None:
            products = {tag.removeprefix(prefix) for tag in ticket.tags if tag.startswith(prefix)}
            # Product tags come from the browser, so only a single other product is spared.
            if len(products) == 1 and not products.intersection(product_slugs):
                continue
        client.add_ticket_tags(ticket.id, [CHAT_REVOKED_TAG])


def revoke_chat_tickets(user, *, product_slugs=None, using=None) -> None:
    """Queue tag_revoked_chat_tickets for once the current change is saved.

    The Zendesk user id is read now, because deleting the user erases it before
    the task runs.
    """
    try:
        zendesk_id = user.profile.zendesk_id
    except Profile.DoesNotExist:
        return

    if zendesk_id:
        before = timezone.now().isoformat()
        products = sorted(product_slugs) if product_slugs is not None else None
        # Using robust prevents a queueing failure from ruining the commit.
        transaction.on_commit(
            lambda remote_id=zendesk_id: tag_revoked_chat_tickets.delay(
                remote_id, product_slugs=products, before=before
            ),
            using=using,
            robust=True,
        )


def chat_coverages(*, include_expired=False):
    """Active chat coverages in effect today, plus those within the expiry cleanup window."""
    today = timezone.localdate()
    since = today - timedelta(days=CHAT_EXPIRY_WINDOW_DAYS) if include_expired else today
    return SupportCoverage.objects.filter(
        contract__status=SupportContract.Status.ACTIVE,
        contract__starts_on__lte=today,
        contract__ends_on__gte=since,
        includes_chat=True,
    )


def had_chat(group_profiles) -> bool:
    """Include recently expired grants so departures cannot escape the daily expiry cleanup."""
    return (
        chat_coverages(include_expired=True).filter(contract__company__in=group_profiles).exists()
    )


def chat_product_slugs(company, *, include_expired=False) -> set[str]:
    return set(
        chat_coverages(include_expired=include_expired)
        .filter(contract__company=company)
        .values_list("product__slug", flat=True)
    )


def revoke_company_chat_tickets(company, product_slugs, using=None) -> None:
    """Queue tagging for the active members of the company or its departments."""
    members = (
        User.objects.db_manager(using)
        .filter(groups__profile__in=GroupProfile.objects.get_tree(company), is_active=True)
        .select_related("profile")
        .distinct()
    )
    for user in members:
        revoke_chat_tickets(user, product_slugs=product_slugs, using=using)


@shared_task
@skip_if_read_only_mode
def revoke_expired_chat() -> None:
    """Tag the chats of companies whose chat coverage ran out in the past week.

    Saving a contract can't observe its end date passing, so this runs daily. The week
    covers skipped runs; tagging again is harmless.
    """
    today = timezone.localdate()
    expired = defaultdict(set)
    for company_id, product_slug in SupportCoverage.objects.filter(
        includes_chat=True,
        contract__status=SupportContract.Status.ACTIVE,
        contract__ends_on__range=(
            today - timedelta(days=CHAT_EXPIRY_WINDOW_DAYS),
            today - timedelta(days=1),
        ),
    ).values_list("contract__company_id", "product__slug"):
        expired[company_id].add(product_slug)
    for company in GroupProfile.objects.filter(pk__in=expired.keys()):
        # A renewal in effect today keeps chat for the products it covers.
        if products := expired[company.pk] - chat_product_slugs(company):
            revoke_company_chat_tickets(company, products)


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
    Creation events matter only for live chats, which SUMO picks up as they start.
    """
    if not (detail := payload.get("detail")) or not (ticket_id := detail.get("id")):
        raise ValueError("Zendesk webhook payload missing detail.id.")

    event_type = payload.get("type")
    if event_type not in HANDLED_EVENT_TYPES:
        log.warning(f"Unhandled Zendesk event type: {event_type or 'missing'}.")
        return

    if event_type == CREATED_EVENT_TYPE:
        # Tickets sent from SUMO already have a SupportTicket, so only tickets created
        # via messaging are handled here.
        if (detail.get("via") or {}).get("channel") == SupportTicket.ZD_CHANNEL_MESSAGING:
            try:
                zd_ticket = ZendeskClient().get_ticket(ticket_id)
            except RecordNotFoundException:
                return
            adopt_chat_ticket(zd_ticket)
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


@shared_task
@skip_if_read_only_mode
def adopt_chat_tickets(lookback_days: int = 7) -> None:
    """Pick-up recent live chats that SUMO hasn't yet collected.

    Backup for the webhook, which picks up each chat as it starts. After an outage,
    run it once by hand with a longer lookback_days to catch up.
    """
    created_after = (timezone.now() - timedelta(days=lookback_days)).date()
    zd_tickets = list(ZendeskClient().search_chat_tickets(created_after))

    known_ids = set(
        SupportTicket.objects.filter(
            zendesk_ticket_id__in=[str(zd_ticket.id) for zd_ticket in zd_tickets]
        ).values_list("zendesk_ticket_id", flat=True)
    )

    for zd_ticket in zd_tickets:
        if str(zd_ticket.id) in known_ids:
            continue
        try:
            adopt_chat_ticket(zd_ticket)
        except APIException, ZenpyException, requests.RequestException:
            # Carry on, so one bad chat can't hold up the rest. The next run tries it again.
            log.exception(f"Failed to pick up chat ticket {zd_ticket.id}.")
