#!/usr/bin/env python
import os
import sys

# Now we can import from third-party libraries.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsune.settings_local')
os.environ.setdefault('CELERY_CONFIG_MODULE', 'kitsune.settings_local')
from django.conf import settings

# MONKEYPATCH! WOO HOO!
# Need this so we patch before running Django-specific commands which
# import Jingo and then result in a circular import.
from kitsune.sumo.monkeypatch import patch
patch()

# Import for side-effect: configures our logging handlers.
from kitsune import log_settings

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
