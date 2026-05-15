from datetime import UTC, datetime, timedelta
from unittest import mock

from celery.schedules import crontab, schedule
from django.test.utils import override_settings
from django.utils import timezone

from kitsune.sumo.tests import TestCase
from kitsune.watchdog.core import (
    OverdueTask,
    audit_tasks,
    claim_alerts,
    prune_stale_health_records,
    send_email_alert,
)
from kitsune.watchdog.models import TaskHealth
from kitsune.watchdog.tests import WATCHDOG_SETTINGS, make_health


@override_settings(**WATCHDOG_SETTINGS)
class TestAuditTasks(TestCase):
    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},  # hourly
        }
    )
    def test_detects_overdue_task(self):
        make_health("my_task", last_completed_at=timezone.now() - timedelta(hours=12))

        overdue = audit_tasks()

        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "my_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    def test_skips_recent_task(self):
        make_health("my_task", last_completed_at=timezone.now() - timedelta(minutes=30))

        overdue = audit_tasks()

        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    def test_creates_row_on_first_observation(self):
        """First watchdog run for a task creates the TaskHealth row with no completion."""
        self.assertFalse(TaskHealth.objects.filter(name="my_task").exists())

        audit_tasks()

        self.assertTrue(TaskHealth.objects.filter(name="my_task").exists())

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},  # hourly
        }
    )
    def test_skips_never_completed_within_grace(self):
        """Never-completed task is not overdue if within grace (period * (allowed_missed + 1))."""
        # created 30 minutes ago; allowed_missed=1 -> grace = 2h. 30 min < 2h, so safe.
        make_health("my_task", created_at=timezone.now() - timedelta(minutes=30))

        overdue = audit_tasks()

        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},  # hourly
        }
    )
    def test_alerts_never_completed_past_grace(self):
        """Never-completed task is overdue once grace period elapses."""
        # created 3 hours ago; grace = 2h. 3h > 2h, so overdue.
        make_health("my_task", created_at=timezone.now() - timedelta(hours=3))

        overdue = audit_tasks()

        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "my_task")
        self.assertIsNone(overdue[0].last_completed_at)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "excluded_task": {"task": "some.task", "schedule": crontab(minute="0")},
        },
        WATCHDOG_EXCLUDED_TASKS=["excluded_task"],
    )
    def test_skips_excluded_tasks(self):
        overdue = audit_tasks()

        self.assertEqual(len(overdue), 0)
        self.assertFalse(TaskHealth.objects.filter(name="excluded_task").exists())

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "watchdog": {
                "task": "kitsune.watchdog.tasks.watchdog",
                "schedule": crontab(minute="*/5"),
            },
        }
    )
    def test_skips_itself(self):
        overdue = audit_tasks()

        self.assertEqual(len(overdue), 0)
        self.assertFalse(TaskHealth.objects.filter(name="watchdog").exists())

    @override_settings(CELERY_BEAT_SCHEDULE={})
    def test_empty_schedule_returns_empty(self):
        overdue = audit_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": timedelta(seconds=30)},
        }
    )
    def test_skips_invalid_schedule_value(self):
        """A raw timedelta (not a BaseSchedule subclass) is rejected — copying
        and setting nowfun on it would AttributeError."""
        overdue = audit_tasks()

        self.assertEqual(len(overdue), 0)
        self.assertFalse(TaskHealth.objects.filter(name="my_task").exists())

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": schedule(timedelta(minutes=10))},
        }
    )
    def test_accepts_non_crontab_schedule(self):
        """A non-crontab BaseSchedule (e.g., fixed-interval schedule) is accepted."""
        make_health("my_task", last_completed_at=timezone.now() - timedelta(hours=1))

        overdue = audit_tasks()

        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "my_task")


@override_settings(**WATCHDOG_SETTINGS)
class TestAuditTasksDeadlineCalculation(TestCase):
    """Tests that exercise real crontab schedules to verify deadline math.

    With allowed_missed_runs=1:
        deadline = the 2nd scheduled run strictly after the anchor.

    Anchor is last_completed_at when set, otherwise created_at.
    Time is pinned to a fixed datetime so the deadlines land predictably
    relative to schedule runs, regardless of when CI runs.
    """

    # Pinned: Friday 2026-05-01 00:00:00 UTC.
    # Chosen so common run boundaries (top-of-hour, top-of-day,
    # 6-hour multiples, 1st of month) coincide with `now`.
    NOW = datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC)

    def setUp(self):
        super().setUp()
        patcher = mock.patch("django.utils.timezone.now", return_value=self.NOW)
        patcher.start()
        self.addCleanup(patcher.stop)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "hourly_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    def test_hourly_task_not_overdue_within_grace(self):
        """Hourly task completed 90 min ago: 2nd run is now (00:00). now > now is False."""
        make_health("hourly_task", last_completed_at=self.NOW - timedelta(minutes=90))
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "hourly_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    def test_hourly_task_overdue_past_grace(self):
        """Hourly task completed 3h ago: 2nd run was 1h ago, so overdue."""
        make_health("hourly_task", last_completed_at=self.NOW - timedelta(hours=3))

        overdue = audit_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "hourly_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "frequent_task": {"task": "some.task", "schedule": crontab(minute="*/10")},
        }
    )
    def test_10min_task_not_overdue_at_15min(self):
        make_health("frequent_task", last_completed_at=self.NOW - timedelta(minutes=15))
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "frequent_task": {"task": "some.task", "schedule": crontab(minute="*/10")},
        }
    )
    def test_10min_task_overdue_at_25min(self):
        make_health("frequent_task", last_completed_at=self.NOW - timedelta(minutes=25))

        overdue = audit_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "frequent_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "daily_task": {"task": "some.task", "schedule": crontab(hour="3", minute="0")},
        }
    )
    def test_daily_task_not_overdue_at_30h(self):
        make_health("daily_task", last_completed_at=self.NOW - timedelta(hours=30))
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "daily_task": {"task": "some.task", "schedule": crontab(hour="3", minute="0")},
        }
    )
    def test_daily_task_overdue_at_50h(self):
        make_health("daily_task", last_completed_at=self.NOW - timedelta(hours=50))

        overdue = audit_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "daily_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "six_hourly_task": {
                "task": "some.task",
                "schedule": crontab(hour="*/6", minute="0"),
            },
        }
    )
    def test_6h_task_not_overdue_at_10h(self):
        make_health("six_hourly_task", last_completed_at=self.NOW - timedelta(hours=10))
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "six_hourly_task": {
                "task": "some.task",
                "schedule": crontab(hour="*/6", minute="0"),
            },
        }
    )
    def test_6h_task_overdue_at_14h(self):
        make_health("six_hourly_task", last_completed_at=self.NOW - timedelta(hours=14))

        overdue = audit_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "six_hourly_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "weekly_task": {
                "task": "some.task",
                "schedule": crontab(hour="4", minute="30", day_of_week="0"),
            },
        }
    )
    def test_weekly_task_not_overdue_at_10d(self):
        make_health("weekly_task", last_completed_at=self.NOW - timedelta(days=10))
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "weekly_task": {
                "task": "some.task",
                "schedule": crontab(hour="4", minute="30", day_of_week="0"),
            },
        }
    )
    def test_weekly_task_overdue_at_15d(self):
        make_health("weekly_task", last_completed_at=self.NOW - timedelta(days=15))

        overdue = audit_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "weekly_task")

    # Tri-weekly Sun/Tue/Thu 22:00 — period alternates 2d, 2d, 3d.
    # Verifies the new walk-based deadline logic handles non-uniform schedules
    # correctly. NOW is Fri May 1 00:00 UTC; reference dates: Apr 23/30 = Thu,
    # Apr 26 / May 3 = Sun, Apr 28 / May 5 = Tue.

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "triweekly_task": {
                "task": "some.task",
                "schedule": crontab(hour="22", minute="0", day_of_week="0,2,4"),
            },
        }
    )
    def test_triweekly_task_not_overdue_after_short_gap(self):
        """Anchor Tue 23:00. 1st run Thu 22:00 (~2d), 2nd run Sun 22:00.
        Deadline May 3 22:00 > NOW (May 1 00:00) → not overdue."""
        anchor = datetime(2026, 4, 28, 23, 0, tzinfo=UTC)
        make_health("triweekly_task", last_completed_at=anchor)
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "triweekly_task": {
                "task": "some.task",
                "schedule": crontab(hour="22", minute="0", day_of_week="0,2,4"),
            },
        }
    )
    def test_triweekly_task_not_overdue_after_long_gap(self):
        """Anchor Thu 23:00. 1st run Sun 22:00 (~3d, the long gap),
        2nd run Tue 22:00. Deadline May 5 22:00 > NOW → not overdue.
        Demonstrates the long Thu→Sun gap doesn't cause spurious alerts."""
        anchor = datetime(2026, 4, 30, 23, 0, tzinfo=UTC)
        make_health("triweekly_task", last_completed_at=anchor)
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "triweekly_task": {
                "task": "some.task",
                "schedule": crontab(hour="22", minute="0", day_of_week="0,2,4"),
            },
        }
    )
    def test_triweekly_task_overdue_across_long_gap(self):
        """Anchor Thu Apr 23 23:00. 1st run Sun Apr 26 22:00 (~3d),
        2nd run Tue Apr 28 22:00. Deadline Apr 28 22:00 < NOW → overdue.
        Confirms the long gap is recognized correctly when 2 runs have passed."""
        anchor = datetime(2026, 4, 23, 23, 0, tzinfo=UTC)
        make_health("triweekly_task", last_completed_at=anchor)
        overdue = audit_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "triweekly_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "monthly_task": {
                "task": "some.task",
                "schedule": crontab(day_of_month="1", hour="0", minute="30"),
            },
        }
    )
    def test_monthly_task_not_overdue_at_40d(self):
        make_health("monthly_task", last_completed_at=self.NOW - timedelta(days=40))
        self.assertEqual(len(audit_tasks()), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "monthly_task": {
                "task": "some.task",
                "schedule": crontab(day_of_month="1", hour="0", minute="30"),
            },
        }
    )
    def test_monthly_task_overdue_at_65d(self):
        make_health("monthly_task", last_completed_at=self.NOW - timedelta(days=65))

        overdue = audit_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "monthly_task")


@override_settings(**WATCHDOG_SETTINGS)
class TestPruneStaleHealthRecords(TestCase):
    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "current_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    def test_deletes_stale_rows(self):
        make_health("current_task")
        make_health("removed_task")

        deleted = prune_stale_health_records()

        self.assertEqual(deleted, 1)
        self.assertTrue(TaskHealth.objects.filter(name="current_task").exists())
        self.assertFalse(TaskHealth.objects.filter(name="removed_task").exists())

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "current_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    def test_keeps_current_rows(self):
        make_health("current_task")

        deleted = prune_stale_health_records()

        self.assertEqual(deleted, 0)
        self.assertTrue(TaskHealth.objects.filter(name="current_task").exists())

    @override_settings(CELERY_BEAT_SCHEDULE={})
    def test_noop_on_empty_schedule(self):
        """Safety guard: never wipe the table when the schedule is empty."""
        make_health("some_task")

        deleted = prune_stale_health_records()

        self.assertEqual(deleted, 0)
        self.assertTrue(TaskHealth.objects.filter(name="some_task").exists())

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "current_task": {"task": "some.task", "schedule": crontab(minute="0")},
            "excluded_task": {"task": "other.task", "schedule": crontab(minute="0")},
        },
        WATCHDOG_EXCLUDED_TASKS=["excluded_task"],
    )
    def test_removes_excluded_task_rows(self):
        """Rows for tasks added to WATCHDOG_EXCLUDED_TASKS are pruned, matching
        the unified watched_task_names predicate used by audit_tasks and signals."""
        make_health("current_task")
        make_health("excluded_task")

        deleted = prune_stale_health_records()

        self.assertEqual(deleted, 1)
        self.assertTrue(TaskHealth.objects.filter(name="current_task").exists())
        self.assertFalse(TaskHealth.objects.filter(name="excluded_task").exists())


@override_settings(**WATCHDOG_SETTINGS)
class TestClaimAlerts(TestCase):
    def test_claims_when_no_prior_alert(self):
        """A task whose last_alerted_at is None can be claimed."""
        make_health("task_a")

        claimed = claim_alerts(["task_a"])

        self.assertEqual(claimed, {"task_a"})
        health = TaskHealth.objects.get(name="task_a")
        self.assertIsNotNone(health.last_alerted_at)

    def test_does_not_claim_within_throttle(self):
        """A task alerted within the throttle window cannot be re-claimed."""
        recent = timezone.now() - timedelta(hours=1)  # well within 24h throttle
        make_health("task_a")
        TaskHealth.objects.filter(name="task_a").update(last_alerted_at=recent)

        claimed = claim_alerts(["task_a"])

        self.assertEqual(claimed, set())
        # Existing last_alerted_at is not overwritten when the claim fails.
        self.assertEqual(TaskHealth.objects.get(name="task_a").last_alerted_at, recent)

    def test_claims_when_last_alert_outside_throttle(self):
        """A task alerted long enough ago can be re-claimed."""
        old = timezone.now() - timedelta(hours=48)  # outside the 24h throttle
        make_health("task_a")
        TaskHealth.objects.filter(name="task_a").update(last_alerted_at=old)

        claimed = claim_alerts(["task_a"])

        self.assertEqual(claimed, {"task_a"})
        self.assertGreater(TaskHealth.objects.get(name="task_a").last_alerted_at, old)

    def test_claims_subset_when_some_throttled(self):
        """In a batch, returns only the names actually claimed."""
        now = timezone.now()
        make_health("fresh_task")  # never alerted
        make_health("recently_alerted_task")
        TaskHealth.objects.filter(name="recently_alerted_task").update(
            last_alerted_at=now - timedelta(hours=1)
        )

        claimed = claim_alerts(["fresh_task", "recently_alerted_task"])

        self.assertEqual(claimed, {"fresh_task"})

    def test_empty_input_returns_empty_set(self):
        self.assertEqual(claim_alerts([]), set())


@override_settings(**WATCHDOG_SETTINGS)
class TestSendEmailAlert(TestCase):
    @mock.patch("kitsune.watchdog.core.send_mail")
    def test_sends_email_for_completed_task(self, mock_send_mail):
        now = timezone.now()
        overdue_tasks = [
            OverdueTask("my_task", now - timedelta(hours=12), now - timedelta(hours=11)),
        ]

        send_email_alert(overdue_tasks)

        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args
        self.assertIn("1 task(s) overdue", args[0][0])
        self.assertIn("my_task", args[0][1])
        self.assertIn("Last completed:", args[0][1])
        self.assertEqual(args[0][3], ["test@example.com"])

    @mock.patch("kitsune.watchdog.core.send_mail")
    def test_email_says_never_for_uncompleted_task(self, mock_send_mail):
        now = timezone.now()
        overdue_tasks = [OverdueTask("my_task", None, now - timedelta(hours=1))]

        send_email_alert(overdue_tasks)

        args = mock_send_mail.call_args
        self.assertIn("Last completed: never", args[0][1])

    @override_settings(WATCHDOG_EMAIL_RECIPIENTS=[])
    @mock.patch("kitsune.watchdog.core.send_mail")
    def test_skips_when_no_recipients(self, mock_send_mail):
        now = timezone.now()
        send_email_alert([OverdueTask("task", now - timedelta(hours=12), now)])
        mock_send_mail.assert_not_called()
