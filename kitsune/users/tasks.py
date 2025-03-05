import json
from datetime import datetime, timedelta

import waffle
from celery import shared_task

from kitsune.products.models import Product
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.users.auth import FXAAuthBackend
from kitsune.users.models import AccountEvent
from kitsune.users.utils import anonymize_user, delete_user_pipeline

shared_task_with_retry = shared_task(
    acks_late=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs=dict(max_retries=4)
)


@shared_task_with_retry
@skip_if_read_only_mode
def process_event_delete_user(event_id):
    event = AccountEvent.objects.get(id=event_id)
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
@skip_if_read_only_mode
def process_event_subscription_state_change(event_id):
    event = AccountEvent.objects.get(id=event_id)
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
@skip_if_read_only_mode
def process_event_password_change(event_id):
    event = AccountEvent.objects.get(id=event_id)
    body = json.loads(event.body)

    change_time = datetime.utcfromtimestamp(body["changeTime"] / 1000.0)

    if event.profile.fxa_password_change and event.profile.fxa_password_change > change_time:
        event.status = AccountEvent.IGNORED
        event.save()
        return

    event.profile.fxa_password_change = change_time
    event.profile.save()
    event.status = AccountEvent.PROCESSED
    event.save()


@shared_task_with_retry
@skip_if_read_only_mode
def process_event_profile_change(event_id):
    event = AccountEvent.objects.get(id=event_id)
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
def process_unprocessed_account_events(days):
    """
    Attempt to process all unprocessed account events that have been
    created within the past "days" number of days.
    """
    days_ago = datetime.now() - timedelta(days=days)

    for event in AccountEvent.objects.filter(
        status=AccountEvent.UNPROCESSED, created_at__gte=days_ago
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
