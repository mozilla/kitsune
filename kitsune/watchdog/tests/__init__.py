from kitsune.watchdog.models import TaskHealth

WATCHDOG_SETTINGS = {
    "WATCHDOG_EMAIL_RECIPIENTS": ["test@example.com"],
    "WATCHDOG_ALLOWED_MISSED_RUNS": 1,
    "WATCHDOG_ALERT_THROTTLE": 24,
    "WATCHDOG_EXCLUDED_TASKS": ["watchdog"],
}


def make_health(name, created_at=None, last_completed_at=None):
    """Create a TaskHealth row, overriding auto_now_add for created_at when given."""
    health = TaskHealth.objects.create(name=name, last_completed_at=last_completed_at)
    if created_at is not None:
        TaskHealth.objects.filter(name=name).update(created_at=created_at)
        health.refresh_from_db()
    return health
