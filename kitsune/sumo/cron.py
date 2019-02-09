from datetime import datetime

import cronjobs

from kitsune.sumo.tasks import measure_queue_lag


@cronjobs.register
def enqueue_lag_monitor_task():
    """Fires a task that measures the queue lag."""
    measure_queue_lag.delay(datetime.now())
