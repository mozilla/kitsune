import logging
from datetime import datetime

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from post_office.tasks import cleanup_mail, send_queued_mail

from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.sumo.watchdog import get_overdue_tasks, send_email_alert, try_alert

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


@shared_task
def watchdog():
    """Check all beat-scheduled tasks for overdue runs and alert if any are missing."""
    if not settings.WATCHDOG_EMAIL_RECIPIENTS:
        return

    overdue_tasks = get_overdue_tasks()
    if not overdue_tasks:
        return

    try:
        redis_conn = redis_client("default")
    except RedisError:
        log.exception("Redis unavailable for watchdog alert suppression")
        redis_conn = None

    tasks_to_alert = []
    for task in overdue_tasks:
        if try_alert(task.name, redis_conn):
            tasks_to_alert.append(task)

    if tasks_to_alert:
        send_email_alert(tasks_to_alert)
        log.warning(
            "Celery beat watchdog: %d task(s) overdue: %s",
            len(tasks_to_alert),
            ", ".join(t.name for t in tasks_to_alert),
        )
