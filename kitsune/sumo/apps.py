from django.apps.config import AppConfig

from kitsune.sumo.monkeypatch import patch  # noqa

# MONKEYPATCH! WOO HOO! LULZ
patch()


class SumoConfig(AppConfig):
    name = "kitsune.sumo"


class ProgrammingError(Exception):
    """Somebody made a mistake in the code."""
