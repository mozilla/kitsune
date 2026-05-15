import copy
import logging
from datetime import datetime, timedelta
from typing import NamedTuple

from celery.schedules import BaseSchedule
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.timesince import timesince

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


def watched_task_names():
    """Return the set of beat-schedule task names the watchdog actively monitors."""
    return {
        name
        for name, cfg in settings.CELERY_BEAT_SCHEDULE.items()
        if name not in settings.WATCHDOG_EXCLUDED_TASKS
        and isinstance(cfg["schedule"], BaseSchedule)
    }


def audit_tasks():
    """Return overdue tasks, creating a TaskHealth row for any watched task
    that doesn't yet have one.

    A task is overdue once (WATCHDOG_ALLOWED_MISSED_RUNS + 1) scheduled runs
    have passed since its anchor without a successful completion. The anchor
    is the task's last_completed_at if it's ever succeeded, or its created_at
    if it hasn't — so newly-observed tasks get an implicit per-task grace
    period proportional to their schedule's interval.
    """
    watched_names = watched_task_names()
    if not watched_names:
        return []

    TaskHealth.objects.bulk_create(
        [TaskHealth(name=name) for name in watched_names],
        ignore_conflicts=True,
    )
    healths = {h.name: h for h in TaskHealth.objects.filter(name__in=watched_names)}

    now = timezone.now()
    n = settings.WATCHDOG_ALLOWED_MISSED_RUNS + 1
    overdue = []

    for name, cfg in settings.CELERY_BEAT_SCHEDULE.items():
        if name not in watched_names:
            continue
        schedule = cfg["schedule"]
        health = healths[name]
        anchor = health.last_completed_at or health.created_at
        deadline = nth_run_after(schedule, anchor, n)

        if now > deadline:
            expected_next_run = next_run_after(schedule, anchor)
            overdue.append(OverdueTask(name, health.last_completed_at, expected_next_run))

    return overdue


def prune_stale_health_records():
    """Delete TaskHealth rows for tasks the watchdog no longer monitors.

    Guarded against an empty watched set to avoid wiping the table during a
    misconfigured settings load.
    """
    watched_names = watched_task_names()
    if not watched_names:
        return 0

    deleted, _ = TaskHealth.objects.exclude(name__in=watched_names).delete()
    if deleted:
        log.info(f"Watchdog pruned {deleted} stale TaskHealth row(s).")
    return deleted


def claim_alerts(task_names):
    """Atomically claim alert slots for all given tasks not currently throttled.

    Returns the set of task names that won the claim.
    """
    if not task_names:
        return set()
    now = timezone.now()
    cutoff = now - timedelta(hours=settings.WATCHDOG_ALERT_THROTTLE)
    with transaction.atomic():
        claimed = set(
            TaskHealth.objects.select_for_update()
            .filter(name__in=task_names)
            .filter(Q(last_alerted_at__isnull=True) | Q(last_alerted_at__lt=cutoff))
            .values_list("name", flat=True)
        )
        if claimed:
            TaskHealth.objects.filter(name__in=claimed).update(last_alerted_at=now)
    return claimed


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
