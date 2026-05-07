from django.apps import AppConfig


class WatchdogConfig(AppConfig):
    name = "kitsune.watchdog"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        # Connect Celery signal handlers (import has side effects).
        from kitsune.watchdog import signals  # noqa: F401
