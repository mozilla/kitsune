from datetime import timedelta
from unittest import mock

from celery.schedules import crontab
from django.core.exceptions import ObjectDoesNotExist
from django.test.utils import override_settings
from django.utils import timezone

from kitsune.sumo.tests import TestCase
from kitsune.sumo.watchdog import OverdueTask, get_overdue_tasks, send_email_alert

WATCHDOG_SETTINGS = {
    "WATCHDOG_EMAIL_RECIPIENTS": ["test@example.com"],
    "WATCHDOG_ALLOWED_MISSED_RUNS": 1,
    "WATCHDOG_ALERT_COOLDOWN_SECONDS": 86400,
    "WATCHDOG_EXCLUDED_TASKS": [],
}


@override_settings(**WATCHDOG_SETTINGS)
class TestGetOverdueTasks(TestCase):
    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),  # hourly
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_detects_overdue_task(self, MockPeriodicTask):
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=12)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "my_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),  # hourly
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_skips_recent_task(self, MockPeriodicTask):
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(minutes=30)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_skips_null_last_run_at(self, MockPeriodicTask):
        mock_task = mock.Mock()
        mock_task.last_run_at = None
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_skips_task_not_in_db(self, MockPeriodicTask):
        MockPeriodicTask.DoesNotExist = ObjectDoesNotExist
        MockPeriodicTask.objects.get.side_effect = ObjectDoesNotExist

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "excluded_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),
            },
        },
        WATCHDOG_EXCLUDED_TASKS=["excluded_task"],
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_skips_excluded_tasks(self, MockPeriodicTask):
        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)
        MockPeriodicTask.objects.get.assert_not_called()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "watchdog": {
                "task": "kitsune.sumo.tasks.watchdog",
                "schedule": crontab(minute="*/5"),
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_skips_itself(self, MockPeriodicTask):
        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)
        MockPeriodicTask.objects.get.assert_not_called()

    @override_settings(CELERY_BEAT_SCHEDULE={})
    def test_empty_schedule_returns_empty(self):
        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {
                "task": "some.task",
                "schedule": timedelta(seconds=30),
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_skips_non_crontab_schedule(self, MockPeriodicTask):
        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)
        MockPeriodicTask.objects.get.assert_not_called()


@override_settings(**WATCHDOG_SETTINGS)
class TestGetOverdueTasksDeadlineCalculation(TestCase):
    """Tests that exercise real crontab.remaining_delta to verify deadline math.

    With allowed_missed_runs=1:
        deadline = last_run_at + period * 2

    The period is computed from "now" via remaining_delta, so it's always
    the true schedule period. The deadline is exactly 2 * period after
    last_run_at.
    """

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "hourly_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),  # hourly, period=1h
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_hourly_task_not_overdue_within_grace(self, MockPeriodicTask):
        """Hourly task 90 min ago: deadline = last_run + 2h, so 90 min is safe."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(minutes=90)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "hourly_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),  # hourly, period=1h
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_hourly_task_overdue_past_grace(self, MockPeriodicTask):
        """Hourly task 3h ago: deadline = last_run + 2h, so 3h is overdue."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=3)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "hourly_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "frequent_task": {
                "task": "some.task",
                "schedule": crontab(minute="*/10"),  # every 10 min, period=10min
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_10min_task_not_overdue_at_15min(self, MockPeriodicTask):
        """10-min task 15 min ago: deadline = last_run + 20min, so 15min is safe."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(minutes=15)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "frequent_task": {
                "task": "some.task",
                "schedule": crontab(minute="*/10"),  # every 10 min, period=10min
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_10min_task_overdue_at_25min(self, MockPeriodicTask):
        """10-min task 25 min ago: deadline = last_run + 20min, so 25min is overdue."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(minutes=25)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "frequent_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "daily_task": {
                "task": "some.task",
                "schedule": crontab(hour="3", minute="0"),  # daily, period=24h
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_daily_task_not_overdue_at_30h(self, MockPeriodicTask):
        """Daily task 30h ago: deadline = last_run + 48h, so 30h is safe."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=30)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "daily_task": {
                "task": "some.task",
                "schedule": crontab(hour="3", minute="0"),  # daily, period=24h
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_daily_task_overdue_at_50h(self, MockPeriodicTask):
        """Daily task 50h ago: deadline = last_run + 48h, so 50h is overdue."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=50)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "daily_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "six_hourly_task": {
                "task": "some.task",
                "schedule": crontab(hour="*/6", minute="0"),  # every 6h, period=6h
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_6h_task_not_overdue_at_10h(self, MockPeriodicTask):
        """6-hourly task 10h ago: deadline = last_run + 12h, so 10h is safe."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=10)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "six_hourly_task": {
                "task": "some.task",
                "schedule": crontab(hour="*/6", minute="0"),  # every 6h, period=6h
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_6h_task_overdue_at_14h(self, MockPeriodicTask):
        """6-hourly task 14h ago: deadline = last_run + 12h, so 14h is overdue."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=14)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "six_hourly_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "weekly_task": {
                "task": "some.task",
                "schedule": crontab(hour="4", minute="30", day_of_week="0"),  # weekly, period=7d
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_weekly_task_not_overdue_at_10d(self, MockPeriodicTask):
        """Weekly task 10d ago: deadline = last_run + 14d, so 10d is safe."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(days=10)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "weekly_task": {
                "task": "some.task",
                "schedule": crontab(hour="4", minute="30", day_of_week="0"),  # weekly, period=7d
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_weekly_task_overdue_at_15d(self, MockPeriodicTask):
        """Weekly task 15d ago: deadline = last_run + 14d, so 15d is overdue."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(days=15)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "weekly_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "triweekly_task": {
                "task": "some.task",
                "schedule": crontab(
                    hour="22", minute="0", day_of_week="0,2,4"
                ),  # 3x/week, period=2d
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_triweekly_task_not_overdue_at_3d(self, MockPeriodicTask):
        """3x/week task 3d ago: deadline = last_run + 4d, so 3d is safe."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(days=3)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "triweekly_task": {
                "task": "some.task",
                "schedule": crontab(
                    hour="22", minute="0", day_of_week="0,2,4"
                ),  # 3x/week, period=2d
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_triweekly_task_overdue_at_5d(self, MockPeriodicTask):
        """3x/week task 5d ago: deadline = last_run + 4d, so 5d is overdue."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(days=5)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "triweekly_task")

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "monthly_task": {
                "task": "some.task",
                "schedule": crontab(
                    day_of_month="1", hour="0", minute="30"
                ),  # monthly, period=~30d
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_monthly_task_not_overdue_at_40d(self, MockPeriodicTask):
        """Monthly task 40d ago: deadline = last_run + ~60d, so 40d is safe."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(days=40)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 0)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "monthly_task": {
                "task": "some.task",
                "schedule": crontab(
                    day_of_month="1", hour="0", minute="30"
                ),  # monthly, period=~30d
            },
        }
    )
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_monthly_task_overdue_at_65d(self, MockPeriodicTask):
        """Monthly task 65d ago: deadline = last_run + ~60d, so 65d is overdue."""
        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(days=65)
        MockPeriodicTask.objects.get.return_value = mock_task

        overdue = get_overdue_tasks()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].name, "monthly_task")


@override_settings(**WATCHDOG_SETTINGS)
class TestTryAlert(TestCase):
    def test_claims_when_no_prior_alert(self):
        from kitsune.sumo.watchdog import try_alert

        mock_redis = mock.Mock()
        mock_redis.set.return_value = True

        self.assertTrue(try_alert("my_task", mock_redis))
        mock_redis.set.assert_called_once_with("watchdog:alerted:my_task", "1", nx=True, ex=86400)

    def test_does_not_claim_within_cooldown(self):
        from kitsune.sumo.watchdog import try_alert

        mock_redis = mock.Mock()
        mock_redis.set.return_value = False

        self.assertFalse(try_alert("my_task", mock_redis))

    def test_returns_true_when_redis_conn_is_none(self):
        from kitsune.sumo.watchdog import try_alert

        self.assertTrue(try_alert("my_task", None))

    def test_returns_true_on_redis_connection_error(self):
        from redis import ConnectionError as RedisConnectionError

        from kitsune.sumo.watchdog import try_alert

        mock_redis = mock.Mock()
        mock_redis.set.side_effect = RedisConnectionError("connection refused")

        self.assertTrue(try_alert("my_task", mock_redis))


@override_settings(**WATCHDOG_SETTINGS)
class TestSendEmailAlert(TestCase):
    @mock.patch("kitsune.sumo.watchdog.send_mail")
    def test_sends_email(self, mock_send_mail):
        now = timezone.now()
        overdue_tasks = [
            OverdueTask("my_task", now - timedelta(hours=12), now - timedelta(hours=11)),
        ]

        send_email_alert(overdue_tasks)

        mock_send_mail.assert_called_once()
        args = mock_send_mail.call_args
        self.assertIn("1 task(s) overdue", args[0][0])
        self.assertIn("my_task", args[0][1])
        self.assertEqual(args[0][3], ["test@example.com"])

    @override_settings(WATCHDOG_EMAIL_RECIPIENTS=[])
    @mock.patch("kitsune.sumo.watchdog.send_mail")
    def test_skips_when_no_recipients(self, mock_send_mail):
        now = timezone.now()
        send_email_alert(
            [OverdueTask("task", now - timedelta(hours=12), now - timedelta(hours=11))]
        )
        mock_send_mail.assert_not_called()


@override_settings(**WATCHDOG_SETTINGS)
class TestWatchdog(TestCase):
    @override_settings(CELERY_BEAT_SCHEDULE={})
    @mock.patch("kitsune.sumo.tasks.send_email_alert")
    def test_noop_with_empty_schedule(self, mock_send_email):
        from kitsune.sumo.tasks import watchdog

        watchdog()
        mock_send_email.assert_not_called()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),
            },
        }
    )
    @mock.patch("kitsune.sumo.tasks.try_alert", return_value=True)
    @mock.patch("kitsune.sumo.tasks.send_email_alert")
    @mock.patch("kitsune.sumo.tasks.redis_client")
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_sends_alert_for_overdue_task(
        self, MockPeriodicTask, mock_redis_client, mock_send_email, mock_try_alert
    ):
        from kitsune.sumo.tasks import watchdog

        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=12)
        MockPeriodicTask.objects.get.return_value = mock_task

        watchdog()

        mock_send_email.assert_called_once()
        mock_try_alert.assert_called_once()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {
                "task": "some.task",
                "schedule": crontab(minute="0"),
            },
        }
    )
    @mock.patch("kitsune.sumo.tasks.try_alert", return_value=False)
    @mock.patch("kitsune.sumo.tasks.send_email_alert")
    @mock.patch("kitsune.sumo.tasks.redis_client")
    @mock.patch("kitsune.sumo.watchdog.PeriodicTask")
    def test_suppresses_alert_within_cooldown(
        self, MockPeriodicTask, mock_redis_client, mock_send_email, mock_try_alert
    ):
        from kitsune.sumo.tasks import watchdog

        mock_task = mock.Mock()
        mock_task.last_run_at = timezone.now() - timedelta(hours=12)
        MockPeriodicTask.objects.get.return_value = mock_task

        watchdog()

        mock_send_email.assert_not_called()
