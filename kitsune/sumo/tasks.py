from datetime import datetime

from celery import task
from django_statsd.clients import statsd

from kitsune.sumo.decorators import timeit


@task()
@timeit
def measure_queue_lag(queued_time):
    """A task that measures the time it was sitting in the queue.

    It saves the data to graphite via statsd.
    """
    lag = datetime.now() - queued_time
    lag = (lag.days * 3600 * 24) + lag.seconds
    statsd.gauge("celery.lag", max(lag, 0))
