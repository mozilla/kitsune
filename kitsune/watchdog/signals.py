from celery.signals import task_success
from django.conf import settings
from django.utils import timezone

from kitsune.watchdog.core import watched_task_names
from kitsune.watchdog.models import TaskHealth


@task_success.connect
def record_task_completion(sender, **kwargs):
    """Record successful completion of a periodic task the watchdog monitors."""
    if sender is None:
        return

    name = settings.CELERY_BEAT_NAME_BY_TASK.get(sender.name)
    if not (name and name in watched_task_names()):
        return

    TaskHealth.objects.update_or_create(
        name=name,
        defaults={"last_completed_at": timezone.now()},
    )
