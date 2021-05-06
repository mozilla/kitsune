import json
from datetime import datetime
from celery import task
from kitsune.users.models import AccountEvent
from kitsune.users.utils import anonymize_user
from kitsune.products.models import Product


@task
def process_event_delete_user(event_id):
    event = AccountEvent.objects.get(id=event_id)

    anonymize_user(event.profile.user)

    event.status = AccountEvent.PROCESSED
    event.save()


@task
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

    products = Product.objects.filter(codename__in=body["capabilities"])
    if body["isActive"]:
        event.profile.products.add(*products)
    else:
        event.profile.products.remove(*products)
    event.status = AccountEvent.PROCESSED
    event.save()


@task
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
