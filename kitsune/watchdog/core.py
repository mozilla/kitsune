import copy
import logging
from datetime import datetime
from typing import NamedTuple

from celery.schedules import crontab
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.timesince import timesince
from redis import ConnectionError as RedisConnectionError

from kitsune.watchdog.models import TaskHealth

log = logging.getLogger("k.watchdog")


class OverdueTask(NamedTuple):
    name: str
    last_completed_at: datetime | None
    expected_next_run: datetime


def next_run_after(schedule, anchor):
    """Return the next scheduled run strictly after anchor.

    Works on a shallow copy of the schedule with nowfun pinned to anchor.
    This is needed because crontab.remaining_delta has a same-day assumption
    (its internal check `last_run_at.day == now.day`) that produces wrong
    results for past anchors with intra-hour schedules — e.g., for
    crontab(minute="*/5") with a 5-day-old anchor at 10:17, it would return
    11:00 instead of 10:20. Pinning now() to the anchor makes the same-day
    check trivially true and the rest of the logic computes correctly.
    """
    pinned = copy.copy(schedule)
    pinned.nowfun = lambda: anchor
    return anchor + pinned.remaining_estimate(anchor)


def nth_run_after(schedule, anchor, n):
    """Return the time of the n-th scheduled run strictly after anchor."""
    run = anchor
    for _ in range(n):
        run = next_run_after(schedule, run)
    return run


def get_overdue_tasks():
    """Return a list of OverdueTask for tasks past their deadline.

    Anchor for the deadline is last_completed_at when set; otherwise
    created_at (the moment the watchdog first observed the task). The
    deadline is the (WATCHDOG_ALLOWED_MISSED_RUNS + 1)-th scheduled run
    strictly after the anchor — i.e., we alert once that many runs have
    elapsed without a successful completion. For newly-observed tasks
    (no completions yet) this same logic gives a per-task grace period
    proportional to the schedule's interval.
    """
    if not settings.CELERY_BEAT_SCHEDULE:
        return []

    excluded = set(settings.WATCHDOG_EXCLUDED_TASKS)
    watched = [
        (name, config["schedule"])
        for name, config in settings.CELERY_BEAT_SCHEDULE.items()
        if name not in excluded and isinstance(config["schedule"], crontab)
    ]
    if not watched:
        return []

    # Ensure a TaskHealth row exists for every watched task with a single
    # bulk insert (ignore_conflicts skips already-existing rows), then fetch
    # them all in one query. Race-safe against the task_success signal
    # handler concurrently inserting rows for the same names.
    watched_names = [name for name, _ in watched]
    TaskHealth.objects.bulk_create(
        [TaskHealth(name=name) for name in watched_names],
        ignore_conflicts=True,
    )
    healths = {h.name: h for h in TaskHealth.objects.filter(name__in=watched_names)}

    now = timezone.now()
    n = settings.WATCHDOG_ALLOWED_MISSED_RUNS + 1
    overdue = []

    for name, schedule in watched:
        health = healths[name]
        anchor = health.last_completed_at or health.created_at
        deadline = nth_run_after(schedule, anchor, n)

        if now > deadline:
            expected_next_run = next_run_after(schedule, anchor)
            overdue.append(OverdueTask(name, health.last_completed_at, expected_next_run))

    return overdue


def prune_stale_health_records():
    """Delete TaskHealth rows whose name is no longer in CELERY_BEAT_SCHEDULE.

    Guarded against an empty schedule to avoid wiping the table during a
    misconfigured settings load.
    """
    beat_schedule = settings.CELERY_BEAT_SCHEDULE
    if not beat_schedule:
        return 0

    deleted, _ = TaskHealth.objects.exclude(name__in=beat_schedule.keys()).delete()
    if deleted:
        log.info(f"Watchdog pruned {deleted} stale TaskHealth row(s).")
    return deleted


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
        last_completed = (
            f"{task.last_completed_at:%Y-%m-%d %H:%M:%S %Z}" if task.last_completed_at else "never"
        )
        overdue_by = timesince(task.expected_next_run)
        lines.append(
            f"- {task.name}\n"
            f"  Last completed: {last_completed}\n"
            f"  Expected next run: {task.expected_next_run:%Y-%m-%d %H:%M:%S %Z}\n"
            f"  Overdue by: {overdue_by}"
        )

    message = "\n\n".join(lines)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
