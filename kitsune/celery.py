import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kitsune.settings")

from celery import Celery  # noqa
from django.conf import settings  # noqa

app = Celery("kitsune")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.task_routes = {
    "post_office.tasks.send_queued_mail": {"queue": "email"},
    "kitsune.tidings.tasks.send_emails": {"queue": "email"},
    "kitsune.messages.tasks.email_private_message": {"queue": "email"},
    "kitsune.announcements.tasks.send_group_email": {"queue": "email"},
    "kitsune.kbadge.tasks.send_award_notification": {"queue": "email"},
    "kitsune.wiki.tasks.send_reviewed_notification": {"queue": "email"},
    "kitsune.wiki.tasks.send_contributor_notification": {"queue": "email"},
}
