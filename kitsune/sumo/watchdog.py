import logging
from datetime import datetime
from typing import NamedTuple

from celery.schedules import crontab
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timesince import timesince
from django_celery_beat.models import PeriodicTask
from redis import ConnectionError as RedisConnectionError

log = logging.getLogger("k.watchdog")


class OverdueTask(NamedTuple):
    name: str
    last_run_at: datetime
    expected_next_run: datetime


def compute_period(schedule):
    """Compute the interval between two consecutive runs of a crontab schedule.

    Uses "remaining_delta" to find two consecutive scheduled times starting
    from now, then returns the gap between them as a timedelta.

    We use now as the reference because "remaining_delta" has an internal
    same-day assumption that produces incorrect results for dates on other days.
    """
    now = timezone.now()
    _, delta_to_next, _ = schedule.remaining_delta(now)
    next_run = now + delta_to_next
    _, delta_after_next, _ = schedule.remaining_delta(next_run)
    return (next_run + delta_after_next) - next_run


def get_overdue_tasks():
    """Return a list of OverdueTask for tasks that have missed their expected run."""
    beat_schedule = settings.CELERY_BEAT_SCHEDULE
    if not beat_schedule:
        return []

    now = timezone.now()
    excluded = set(settings.WATCHDOG_EXCLUDED_TASKS)
    overdue = []

    for task_name, task_config in beat_schedule.items():
        if task_name == "watchdog":
            continue
        if task_name in excluded:
            continue

        schedule = task_config["schedule"]

        if not isinstance(schedule, crontab):
            continue

        try:
            periodic_task = PeriodicTask.objects.get(name=task_name)
        except PeriodicTask.DoesNotExist:
            continue

        last_run_at = periodic_task.last_run_at
        if last_run_at is None:
            continue

        period = compute_period(schedule)

        deadline = last_run_at + (period * (settings.WATCHDOG_ALLOWED_MISSED_RUNS + 1))

        if now > deadline:
            expected_next_run = last_run_at + period
            overdue.append(OverdueTask(task_name, last_run_at, expected_next_run))

    return overdue


def try_alert(task_name, redis_conn):
    """Atomically check and claim an alert slot for this task.

    Returns True if we should send an alert (no recent alert exists),
    False if an alert was already sent within the cooldown period.
    """
    if not redis_conn:
        return True

    key = f"watchdog:alerted:{task_name}"

    try:
        return redis_conn.set(key, "1", nx=True, ex=settings.WATCHDOG_ALERT_COOLDOWN_SECONDS)
    except RedisConnectionError:
        log.exception("Redis unavailable for alert suppression")
        return True


def send_email_alert(overdue_tasks):
    """Send an email alert for overdue tasks."""
    recipients = settings.WATCHDOG_EMAIL_RECIPIENTS
    if not recipients:
        return

    subject = f"Celery Beat Watchdog: {len(overdue_tasks)} task(s) overdue"
    lines = []
    for task in overdue_tasks:
        overdue_by = timesince(task.expected_next_run)
        lines.append(
            f"- {task.name}\n"
            f"  Last run: {task.last_run_at:%Y-%m-%d %H:%M:%S %Z}\n"
            f"  Expected next run: {task.expected_next_run:%Y-%m-%d %H:%M:%S %Z}\n"
            f"  Overdue by: {overdue_by}"
        )

    message = "\n\n".join(lines)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
