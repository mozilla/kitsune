from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class RetrievalConfig(AppConfig):
    # `default` so INSTALLED_APPS can name the module like every other app: naming this class
    # there instead breaks anything that walks INSTALLED_APPS expecting importable modules.
    default = True
    name = "kitsune.retrieval"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.retrieval.checks import task_timing_problems

        # Raise rather than only reporting: a Celery worker start-up does not necessarily run
        # Django system checks, and a lease that can lapse mid-write is not a warning.
        if problems := task_timing_problems():
            raise ImproperlyConfigured("; ".join(problems))

        if settings.RETRIEVAL_INGESTION_ENABLED:
            from kitsune.retrieval import signals  # noqa: F401  (registers receivers)
