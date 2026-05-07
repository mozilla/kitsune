from datetime import timedelta
from unittest import mock

from celery.schedules import crontab
from django.test.utils import override_settings
from django.utils import timezone

from kitsune.sumo.redis_utils import RedisError
from kitsune.sumo.tests import TestCase
from kitsune.watchdog.models import TaskHealth
from kitsune.watchdog.tasks import watchdog
from kitsune.watchdog.tests import WATCHDOG_SETTINGS, make_health


@override_settings(**WATCHDOG_SETTINGS)
class TestWatchdog(TestCase):
    @override_settings(CELERY_BEAT_SCHEDULE={})
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    def test_noop_with_empty_schedule(self, mock_send_email):
        watchdog()
        mock_send_email.assert_not_called()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    @mock.patch("kitsune.watchdog.tasks.try_alert", return_value=True)
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    @mock.patch("kitsune.watchdog.tasks.redis_client")
    def test_sends_alert_for_overdue_task(
        self, mock_redis_client, mock_send_email, mock_try_alert
    ):
        make_health("my_task", last_completed_at=timezone.now() - timedelta(hours=12))

        watchdog()

        mock_send_email.assert_called_once()
        mock_try_alert.assert_called_once()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    @mock.patch("kitsune.watchdog.tasks.try_alert", return_value=False)
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    @mock.patch("kitsune.watchdog.tasks.redis_client")
    def test_suppresses_alert_within_cooldown(
        self, mock_redis_client, mock_send_email, mock_try_alert
    ):
        make_health("my_task", last_completed_at=timezone.now() - timedelta(hours=12))

        watchdog()

        mock_send_email.assert_not_called()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    @mock.patch(
        "kitsune.watchdog.tasks.redis_client", side_effect=RedisError("connection refused")
    )
    def test_sends_alert_when_redis_unavailable(self, mock_redis_client, mock_send_email):
        """When redis_client raises RedisError, watchdog falls back to alerting
        without cooldown dedup (since try_alert(name, None) returns True)."""
        make_health("my_task", last_completed_at=timezone.now() - timedelta(hours=12))

        watchdog()  # must not raise

        mock_send_email.assert_called_once()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "current_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    @mock.patch("kitsune.watchdog.tasks.try_alert", return_value=True)
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    @mock.patch("kitsune.watchdog.tasks.redis_client")
    def test_prunes_stale_rows(self, mock_redis_client, mock_send_email, mock_try_alert):
        make_health("current_task", last_completed_at=timezone.now())
        make_health("removed_task", last_completed_at=timezone.now())

        watchdog()

        self.assertTrue(TaskHealth.objects.filter(name="current_task").exists())
        self.assertFalse(TaskHealth.objects.filter(name="removed_task").exists())
