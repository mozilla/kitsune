from django.apps import AppConfig


class CustomerCareConfig(AppConfig):
    name = "kitsune.customercare"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.customercare import signals  # noqa
