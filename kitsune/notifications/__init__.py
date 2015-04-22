from django.apps import AppConfig
from django.contrib.auth.models import User

import actstream.registry


default_app_config = 'kitsune.notifications.NotificationsConfig'


class NotificationsConfig(AppConfig):
    name = 'kitsune.notifications'

    def ready(self):
        actstream.registry.register(User)
