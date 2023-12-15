import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kitsune.settings")

from celery import Celery  # noqa
from django.conf import settings  # noqa

app = Celery("kitsune")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.task_routes = {
    "kitusne.announcements.tasks.send_group_email": {"queue": "priority"},
    "kitsune.messages.tasks.email_private_message": {"queue": "priority"},
    "kitsune.tidings.tasks.send_emails": {"queue": "priority"},
    "kitsune.messages.tasks.email_private_messages": {"queue": "priority"},
}
