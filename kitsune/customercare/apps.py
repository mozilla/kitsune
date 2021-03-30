from django.apps import AppConfig


class CustomerCareConfig(AppConfig):
    name = "kitsune.customercare"

    def ready(self):
        from kitsune.customercare.badges import register_signals

        # register signals for badges
        register_signals()
