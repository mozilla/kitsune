import logging

from celery import shared_task
from django.conf import settings

from kitsune.watchdog.core import (
    audit_tasks,
    claim_alerts,
    prune_stale_health_records,
    send_email_alert,
)

log = logging.getLogger("k.task")


@shared_task
def watchdog():
    """Check all beat-scheduled tasks for overdue runs and alert if any are missing."""
    if not settings.WATCHDOG_EMAIL_RECIPIENTS:
        return

    prune_stale_health_records()

    overdue_tasks = audit_tasks()
    if not overdue_tasks:
        return

    claimed = claim_alerts([task.name for task in overdue_tasks])
    tasks_to_alert = [task for task in overdue_tasks if task.name in claimed]

    if tasks_to_alert:
        send_email_alert(tasks_to_alert)
        log.warning(
            "Celery beat watchdog: %d task(s) overdue: %s",
            len(tasks_to_alert),
            ", ".join(t.name for t in tasks_to_alert),
        )
