from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "kitsune.notifications"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import actstream.registry
        from django.contrib.auth.models import User

        actstream.registry.register(User)
