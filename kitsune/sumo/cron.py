from datetime import datetime

from django.conf import settings
from django.core.mail import mail_admins

import cronjobs
import requests
from statsd import statsd

from kitsune.sumo.utils import rabbitmq_queue_size
from kitsune.sumo.tasks import measure_queue_lag


@cronjobs.register
def record_queue_size():
    """Records the rabbitmq size in statsd"""
    statsd.gauge('rabbitmq.size', rabbitmq_queue_size())


@cronjobs.register
def enqueue_lag_monitor_task():
    """Fires a task that measures the queue lag."""
    measure_queue_lag.delay(datetime.now())


@cronjobs.register
def send_postatus_errors():
    """Looks at postatus file and sends an email with errors"""

    # Gah! Don't do this on stage!
    if settings.STAGE:
        return

    def new_section(line):
        return (line.startswith('dennis ')
                or line.startswith('Totals')
                or line.startswith('BUSTED')
                or line.startswith('COMPILED'))

    # Download the postatus file
    postatus = requests.get('https://support.mozilla.org/media/postatus.txt')

    # Parse it to see which locales have issues
    lines = postatus.content.splitlines()
    datestamp = lines.pop(0)

    errordata = []

    while lines:
        line = lines.pop(0)
        if line.startswith('>>> '):
            while lines and not new_section(line):
                errordata.append(line)
                line = lines.pop(0)

    # If we have errors to send, send them
    if errordata:
        mail_admins(
            subject='[SUMO] postatus errors %s' % datestamp,
            message=(
                'These are the errors in the SUMO postatus file:\n\n' +
                '\n'.join(errordata)
                )
            )
