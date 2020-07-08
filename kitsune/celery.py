import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kitsune.settings")

from celery import Celery  # noqa
from django.conf import settings  # noqa

app = Celery("kitsune")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
