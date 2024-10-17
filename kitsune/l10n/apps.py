from django.apps import AppConfig


class L10nConfig(AppConfig):
    name = "kitsune.l10n"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        import kitsune.l10n.signals  # noqa
