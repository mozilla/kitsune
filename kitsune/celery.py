import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kitsune.settings")

from celery import Celery  # noqa
from django.conf import settings  # noqa

app = Celery("kitsune")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.broker_transport_options = {
    'queue_order_strategy': 'priority'
}
app.conf.task_default_priority = 5
app.conf.task_inherit_parent_priority = True
app.conf.task_routes = {
    'kitsune.users.tasks.process_event_*': {
        'queue': 'fxa',
    }
}
app.autodiscover_tasks()
