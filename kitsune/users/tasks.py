from celery import task
from kitsune.sumo.decorators import timeit
from kitsune.users.models import AccountEvent


@task
@timeit
def process_account_event(account_event):
    account_event.process()


@task
@timeit
def process_unprocessed_account_events():
    events = AccountEvent.objects.filter(status=AccountEvent.UNPROCESSED)

    for event in events:
        process_account_event.delay(event)
