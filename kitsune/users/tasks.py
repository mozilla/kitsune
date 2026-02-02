import json
import logging
from datetime import UTC, datetime, timedelta

import waffle
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from kitsune.products.models import Product
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.users.auth import FXAAuthBackend
from kitsune.users.models import AccountEvent
from kitsune.users.utils import anonymize_user, delete_user_pipeline

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3}
)

log = logging.getLogger("k.task")


@shared_task_with_retry
@transaction.atomic
def process_event_delete_user(event_id):
    try:
        event = AccountEvent.objects.get(id=event_id, status=AccountEvent.UNPROCESSED)
    except AccountEvent.DoesNotExist:
        return

    user = event.profile.user
    event.profile = None
    event.save(update_fields=["profile"])

    if waffle.switch_is_active("enable-account-deletion"):
        delete_user_pipeline(user)
    else:
        anonymize_user(user)

    event.status = AccountEvent.PROCESSED
    event.save()


@shared_task_with_retry
@transaction.atomic
def process_event_subscription_state_change(event_id):
    try:
        event = AccountEvent.objects.get(id=event_id, status=AccountEvent.UNPROCESSED)
    except AccountEvent.DoesNotExist:
        return

    body = json.loads(event.body)

    last_event = AccountEvent.objects.filter(
        profile_id=event.profile.pk,
        status=AccountEvent.PROCESSED,
        event_type=AccountEvent.SUBSCRIPTION_STATE_CHANGE,
    ).first()
    if last_event:
        last_event_body = json.loads(last_event.body)
        if last_event_body["changeTime"] > body["changeTime"]:
            event.status = AccountEvent.IGNORED
            event.save()
            return

    products = Product.active.filter(codename__in=body["capabilities"])
    if body["isActive"]:
        event.profile.products.add(*products)
    else:
        event.profile.products.remove(*products)
    event.status = AccountEvent.PROCESSED
    event.save()


@shared_task_with_retry
@transaction.atomic
def process_event_password_change(event_id):
    try:
        event = AccountEvent.objects.get(id=event_id, status=AccountEvent.UNPROCESSED)
    except AccountEvent.DoesNotExist:
        return

    body = json.loads(event.body)

    change_time = datetime.fromtimestamp(body["changeTime"] / 1000.0, UTC)

    if event.profile.fxa_password_change and event.profile.fxa_password_change > change_time:
        event.status = AccountEvent.IGNORED
        event.save()
        return

    event.profile.fxa_password_change = change_time
    event.profile.save()
    event.status = AccountEvent.PROCESSED
    event.save()


@shared_task_with_retry
@transaction.atomic
def process_event_profile_change(event_id):
    try:
        event = AccountEvent.objects.get(id=event_id, status=AccountEvent.UNPROCESSED)
    except AccountEvent.DoesNotExist:
        return

    refresh_token = event.profile.fxa_refresh_token

    fxa = FXAAuthBackend()
    token_info = fxa.refresh_access_token(refresh_token, ttl=300)

    if not (access_token := token_info.get("access_token")):
        event.status = AccountEvent.IGNORED
        event.save()
        return

    user_info = fxa.get_userinfo(access_token, None, None)
    fxa.update_user(event.profile.user, user_info)

    event.status = AccountEvent.PROCESSED
    event.save()


@shared_task
@skip_if_read_only_mode
def process_unprocessed_account_events(within_hours):
    """
    Attempt to process all unprocessed account events that have been
    created within the given number of hours.
    """
    hours_ago = timezone.now() - timedelta(hours=within_hours)

    for event in AccountEvent.objects.filter(
        status=AccountEvent.UNPROCESSED, created_at__gte=hours_ago
    ):
        match event.event_type:
            case AccountEvent.DELETE_USER:
                process_event_delete_user.delay(event.id)
            case AccountEvent.SUBSCRIPTION_STATE_CHANGE:
                process_event_subscription_state_change.delay(event.id)
            case AccountEvent.PASSWORD_CHANGE:
                process_event_password_change.delay(event.id)
            case AccountEvent.PROFILE_CHANGE:
                process_event_profile_change.delay(event.id)


@shared_task
@skip_if_read_only_mode
def cleanup_old_account_events() -> None:
    """Deletes account events that are older than two years."""
    two_years_ago = timezone.now() - timedelta(days=730)  # 2 years * 365 days
    deleted_count = AccountEvent.objects.filter(created_at__lt=two_years_ago).delete()[0]
    log.info(f"Successfully deleted {deleted_count} old account events")


@shared_task
@skip_if_read_only_mode
def cleanup_expired_users() -> None:
    """Delete users who haven't logged-in for more than settings.USER_INACTIVITY_DAYS days."""
    if not waffle.switch_is_active("cleanup-expired-users"):
        log.info("The cleanup of expired users is not enabled.")
        return

    User = get_user_model()
    expiration_date = timezone.now() - timedelta(days=settings.USER_INACTIVITY_DAYS)

    expired_users = User.objects.filter(last_login__lt=expiration_date)
    log.info(f"Found {expired_users.count()} expired users")

    for user in expired_users:
        delete_user_pipeline(user)
        log.info(f"Deleted user {user.username}")

    log.info(f"Successfully processed {expired_users.count()} expired users")
