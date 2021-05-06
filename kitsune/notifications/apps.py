from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "kitsune.notifications"

    def ready(self):
        from django.contrib.auth.models import User

        import actstream.registry

        actstream.registry.register(User)
