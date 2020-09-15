from django.apps import AppConfig


class SearchV2Config(AppConfig):
    name = "kitsune.search.v2"

    def ready(self):
        from kitsune.search.v2 import signals  # noqa
