from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = "kitsune.groups"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import kitsune.groups.signals  # noqa
