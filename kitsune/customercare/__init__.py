from django.apps import AppConfig

from kitsune.customercare.badges import register_signals


default_app_config = 'kitsune.customercare.CustomerCareConfig'


class CustomerCareConfig(AppConfig):
    name = 'kitsune.customercare'

    def ready(self):
        # register signals for badges
        register_signals()
