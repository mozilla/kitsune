from django.apps.config import AppConfig
from django.utils.translation.trans_real import translation
from django.conf import settings

# MONKEYPATCH! WOO HOO! LULZ
from kitsune.sumo.monkeypatch import patch  # noqa

patch()


class SumoConfig(AppConfig):
    name = "kitsune.sumo"

    def ready(self):
        for lang, fallback in settings.FALLBACK_LANGUAGES.items():
            translation(lang)._fallback = translation(fallback)


class ProgrammingError(Exception):
    """Somebody made a mistake in the code."""
