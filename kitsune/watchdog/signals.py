from celery.signals import task_success
from django.conf import settings
from django.utils import timezone

from kitsune.watchdog.models import TaskHealth


@task_success.connect
def record_task_completion(sender, **kwargs):
    """Record successful completion of a periodic task.

    Filters to tasks present in CELERY_BEAT_SCHEDULE (translated via
    CELERY_BEAT_NAME_BY_TASK) so ad-hoc .delay() calls don't pollute the
    table. Skips tasks in WATCHDOG_EXCLUDED_TASKS, matching the filtering
    in get_overdue_tasks. Updates last_completed_at on the matching
    TaskHealth row, creating it if needed.
    """
    if sender is None or sender.name not in settings.CELERY_BEAT_NAME_BY_TASK:
        return

    name = settings.CELERY_BEAT_NAME_BY_TASK[sender.name]
    if name in settings.WATCHDOG_EXCLUDED_TASKS:
        return

    TaskHealth.objects.update_or_create(
        name=name,
        defaults={"last_completed_at": timezone.now()},
    )
