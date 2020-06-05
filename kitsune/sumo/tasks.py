import logging
from datetime import datetime

from celery import task


log = logging.getLogger('k.task')


@task()
def measure_queue_lag(queued_time):
    """A task that measures the time it was sitting in the queue."""
    lag = datetime.now() - queued_time
    lag = max((lag.days * 3600 * 24) + lag.seconds, 0)
    log.info(f'Measure queue lag task value is {lag}')
