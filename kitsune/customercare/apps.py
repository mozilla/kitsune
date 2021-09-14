from django.apps import AppConfig


class CustomerCareConfig(AppConfig):
    name = "kitsune.customercare"

    def ready(self):
        from kitsune.customercare import signals  # noqa
