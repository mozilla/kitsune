from django.apps import AppConfig

from kitsune.customercare import checks  # noqa: F401 (registers system checks)


class CustomerCareConfig(AppConfig):
    name = "kitsune.customercare"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.customercare import signals  # noqa
