import logging

from celery import shared_task
from django.conf import settings

from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.watchdog.core import (
    get_overdue_tasks,
    prune_stale_health_records,
    send_email_alert,
    try_alert,
)

log = logging.getLogger("k.task")


@shared_task
def watchdog():
    """Check all beat-scheduled tasks for overdue runs and alert if any are missing."""
    if not settings.WATCHDOG_EMAIL_RECIPIENTS:
        return

    prune_stale_health_records()

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
