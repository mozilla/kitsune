from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = "kitsune.search"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from kitsune.search import signals  # noqa
