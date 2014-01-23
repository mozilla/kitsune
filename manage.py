#!/usr/bin/env python
import os
import site
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

prev_sys_path = list(sys.path)

site.addsitedir(path('vendor'))

# Move the new items to the front of sys.path.
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

# Now we can import from third-party libraries.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitsune.settings_local')
os.environ.setdefault('CELERY_CONFIG_MODULE', 'kitsune.settings_local')
from django.conf import settings

# Import for side-effect: configures our logging handlers.
from kitsune import log_settings


if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
