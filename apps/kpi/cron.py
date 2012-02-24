from datetime import datetime, date, timedelta

import cronjobs

from kpi.models import Metric, MetricKind, VISITORS_METRIC_CODE
from sumo.webtrends import Webtrends


@cronjobs.register
def update_visitors_metric():
    """Get new visitor data from webtrends and save."""
    try:
        # Get the latest metric value.
        last_metric = Metric.objects.filter(
            kind__code=VISITORS_METRIC_CODE).order_by('-start')[0]
        # We will start updating the day after the last updated.
        start = last_metric.start + timedelta(days=1)
    except IndexError:
        # There are no metrics yet. Let's start from 2011-01-01
        start = date(2011, 01, 01)

    # We will collect up until yesterday
    end = date.today() - timedelta(days=1)

    visitors = Webtrends.visits(start, end)
    metric_kind = MetricKind.objects.get(code=VISITORS_METRIC_CODE)

    for date_str, visits in visitors.items():
        day = datetime.strptime(date_str,"%Y-%m-%d").date()
        Metric.objects.create(
            kind=metric_kind,
            start=day,
            end=day + timedelta(days=1),
            value=visits)
