from django.apps import AppConfig


class UserConfig(AppConfig):
    name = "kitsune.users"
    label = "users"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from django.contrib.auth.models import User

        from kitsune.users.managers import RegularUserManager

        User.all_users = User.objects

        # Create and initialize the new manager
        new_manager = RegularUserManager()
        new_manager.model = User

        # Check if the original manager has a database specified
        if hasattr(User.all_users, "_db") and User.all_users._db is not None:
            new_manager._db = User.all_users._db

        if hasattr(User.all_users, "_hints"):
            new_manager._hints = User.all_users._hints
        User.objects = new_manager
