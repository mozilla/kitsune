import logging
from datetime import datetime

from celery import shared_task
from django.utils import timezone
from post_office.tasks import cleanup_mail, send_queued_mail

from kitsune.sumo.decorators import skip_if_read_only_mode

log = logging.getLogger("k.task")


@shared_task
def enqueue_lag_monitor():
    """A task that kicks-off a measurement of the task queue lag time."""
    measure_queue_lag.delay(timezone.now().isoformat())


@shared_task
def measure_queue_lag(queued_time):
    """A task that measures the time it was sitting in the queue."""
    lag = timezone.now() - datetime.fromisoformat(queued_time)
    lag = max((lag.days * 3600 * 24) + lag.seconds, 0)
    log.info(f"Measure queue lag task value is {lag}")


@shared_task
@skip_if_read_only_mode
def process_queued_mail():
    """Sends all queued mail until done."""
    send_queued_mail()


@shared_task
@skip_if_read_only_mode
def remove_expired_mail():
    """Removes expired mail."""
    cleanup_mail()
