from datetime import timedelta
from unittest import mock

from celery.schedules import crontab
from django.test.utils import override_settings
from django.utils import timezone

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
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    def test_sends_alert_for_overdue_task(self, mock_send_email):
        make_health("my_task", last_completed_at=timezone.now() - timedelta(hours=12))

        watchdog()

        mock_send_email.assert_called_once()
        # The watchdog should have marked the task as alerted.
        self.assertIsNotNone(TaskHealth.objects.get(name="my_task").last_alerted_at)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    def test_suppresses_alert_within_throttle(self, mock_send_email):
        """A task that's overdue but recently alerted is throttled."""
        recent = timezone.now() - timedelta(hours=1)  # within 24h throttle
        make_health("my_task", last_completed_at=timezone.now() - timedelta(hours=12))
        TaskHealth.objects.filter(name="my_task").update(last_alerted_at=recent)

        watchdog()

        mock_send_email.assert_not_called()

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "current_task": {"task": "some.task", "schedule": crontab(minute="0")},
        }
    )
    @mock.patch("kitsune.watchdog.tasks.send_email_alert")
    def test_prunes_stale_rows(self, mock_send_email):
        make_health("current_task", last_completed_at=timezone.now())
        make_health("removed_task", last_completed_at=timezone.now())

        watchdog()

        self.assertTrue(TaskHealth.objects.filter(name="current_task").exists())
        self.assertFalse(TaskHealth.objects.filter(name="removed_task").exists())
