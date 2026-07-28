from django.apps import AppConfig


class KbadgeConfig(AppConfig):
    name = "kitsune.kbadge"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.kbadge import badges  # noqa: F401
