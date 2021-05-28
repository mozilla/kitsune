from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = "kitsune.search"

    def ready(self):
        from kitsune.search import signals  # noqa
