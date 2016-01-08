#!/usr/bin/env python
import os
import sys
import traceback

# Now we can import from third-party libraries.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsune.settings_local')
os.environ.setdefault('CELERY_CONFIG_MODULE', 'kitsune.settings_local')

# MONKEYPATCH! WOO HOO!
# Need this so we patch before running Django-specific commands which
# then result in a circular import.
try:
    from kitsune.sumo.monkeypatch import patch  # noqa
    patch()
except ImportError:
    print 'OH NOES! There was an import error:'
    print ''
    print ''.join(traceback.format_exception(*sys.exc_info()))
    if 'VIRTUAL_ENV' in os.environ:
        print 'Have you installed requirements? Are they up-to-date?'
    else:
        print 'Have you activated your virtual environment?'
    sys.exit(1)

# Import for side-effect: configures our logging handlers.
from kitsune import log_settings  # noqa

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
