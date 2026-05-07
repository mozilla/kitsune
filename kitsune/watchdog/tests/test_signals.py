from datetime import timedelta
from unittest import mock

from celery.schedules import crontab
from django.test.utils import override_settings
from django.utils import timezone

from kitsune.sumo.tests import TestCase
from kitsune.watchdog.models import TaskHealth
from kitsune.watchdog.signals import record_task_completion
from kitsune.watchdog.tests import WATCHDOG_SETTINGS, make_health


@override_settings(**WATCHDOG_SETTINGS)
class TestRecordTaskCompletion(TestCase):
    """Tests for the task_success signal handler."""

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "myapp.tasks.my_task", "schedule": crontab(minute="0")},
        },
        CELERY_BEAT_NAME_BY_TASK={"myapp.tasks.my_task": "my_task"},
    )
    def test_creates_row_on_first_completion(self):
        sender = mock.Mock(name="myapp.tasks.my_task")
        sender.name = "myapp.tasks.my_task"

        record_task_completion(sender=sender)

        health = TaskHealth.objects.get(name="my_task")
        self.assertIsNotNone(health.last_completed_at)

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "my_task": {"task": "myapp.tasks.my_task", "schedule": crontab(minute="0")},
        },
        CELERY_BEAT_NAME_BY_TASK={"myapp.tasks.my_task": "my_task"},
    )
    def test_updates_existing_row(self):
        old_time = timezone.now() - timedelta(hours=2)
        make_health("my_task", last_completed_at=old_time)

        sender = mock.Mock()
        sender.name = "myapp.tasks.my_task"
        record_task_completion(sender=sender)

        health = TaskHealth.objects.get(name="my_task")
        self.assertGreater(health.last_completed_at, old_time)
        self.assertEqual(TaskHealth.objects.count(), 1)

    @override_settings(CELERY_BEAT_NAME_BY_TASK={})
    def test_skips_non_periodic_task(self):
        sender = mock.Mock()
        sender.name = "myapp.tasks.adhoc"

        record_task_completion(sender=sender)

        self.assertEqual(TaskHealth.objects.count(), 0)

    @override_settings(CELERY_BEAT_NAME_BY_TASK={"myapp.tasks.my_task": "my_task"})
    def test_skips_when_sender_is_none(self):
        record_task_completion(sender=None)
        self.assertEqual(TaskHealth.objects.count(), 0)

    @override_settings(
        CELERY_BEAT_NAME_BY_TASK={"myapp.tasks.excluded": "excluded_task"},
        WATCHDOG_EXCLUDED_TASKS=["excluded_task"],
    )
    def test_skips_excluded_task(self):
        sender = mock.Mock()
        sender.name = "myapp.tasks.excluded"
        record_task_completion(sender=sender)

        self.assertFalse(TaskHealth.objects.filter(name="excluded_task").exists())

    @override_settings(
        CELERY_BEAT_SCHEDULE={
            "display_name": {
                "task": "myapp.tasks.dotted_path",
                "schedule": crontab(minute="0"),
            },
        },
        CELERY_BEAT_NAME_BY_TASK={"myapp.tasks.dotted_path": "display_name"},
    )
    def test_uses_display_name_not_dotted_path(self):
        sender = mock.Mock()
        sender.name = "myapp.tasks.dotted_path"
        record_task_completion(sender=sender)

        self.assertTrue(TaskHealth.objects.filter(name="display_name").exists())
        self.assertFalse(TaskHealth.objects.filter(name="myapp.tasks.dotted_path").exists())
