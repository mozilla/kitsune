from django.apps import AppConfig


class WikiConfig(AppConfig):
    name = "kitsune.wiki"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        # Import signals to register them
        from kitsune.wiki import signals  # noqa: F401 - import for signal registration
        from kitsune.wiki.badges import register_signals

        # register signals for badges
        register_signals()
