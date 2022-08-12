from django.apps.config import AppConfig
from django.conf import settings
from django.utils.translation.trans_real import translation

# MONKEYPATCH! WOO HOO! LULZ
from kitsune.sumo.monkeypatch import patch  # noqa

patch()


class SumoConfig(AppConfig):
    name = "kitsune.sumo"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        for lang, fallback in settings.FALLBACK_LANGUAGES.items():
            translation(lang)._fallback = translation(fallback)


class ProgrammingError(Exception):
    """Somebody made a mistake in the code."""
