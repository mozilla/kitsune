from datetime import datetime

from celery import task
from statsd import statsd


@task()
def measure_queue_lag(queued_time):
    """A task that measures the time it was sitting in the queue.

    It saves the data to graphite via statsd.
    """
    lag = (datetime.now() - queued_time).total_seconds()
    statsd.gauge('rabbitmq.lag', lag if lag > 0 else 0)
