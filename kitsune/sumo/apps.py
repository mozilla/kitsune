from django.apps.config import AppConfig

# MONKEYPATCH! WOO HOO! LULZ
from kitsune.sumo.monkeypatch import patch  # noqa

patch()


class SumoConfig(AppConfig):
    name = "kitsune.sumo"


class ProgrammingError(Exception):
    """Somebody made a mistake in the code."""
