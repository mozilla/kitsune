from django.db import models

from kitsune.sumo.models import ModelBase


class TaskHealth(ModelBase):
    """Tracks the most recent successful completion of a periodic task.

    Populated by a Celery task_success signal handler keyed on task name.
    The watchdog reads this to detect tasks that haven't completed within
    their expected interval. last_completed_at is None until the first
    success is recorded; created_at anchors the deadline math in that case.
    last_alerted_at is set when the watchdog claims an alert slot for the
    task, providing the dedup window controlled by WATCHDOG_ALERT_THROTTLE.
    """

    name = models.CharField(max_length=255, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_completed_at = models.DateTimeField(null=True)
    last_alerted_at = models.DateTimeField(null=True)

    def __str__(self):
        return (
            f"{self.name}: created at {self.created_at},"
            f" last completed at {self.last_completed_at}"
        )
