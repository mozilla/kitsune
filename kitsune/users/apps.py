from django.apps import AppConfig


class UserConfig(AppConfig):
    name = "kitsune.users"
    label = "users"
    default_auto_field = "django.db.models.AutoField"
