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
        # Start updating the day after the last updated.
        start = last_metric.start + timedelta(days=1)
    except IndexError:
        # There are no metrics yet, start from 2011-01-01
        start = date(2011, 01, 01)

    # Collect up until yesterday
    end = date.today() - timedelta(days=1)

    # Get the visitor data from webtrends.
    visitors = Webtrends.visits(start, end)

    # Create the metrics.
    metric_kind = MetricKind.objects.get(code=VISITORS_METRIC_CODE)
    for date_str, visits in visitors.items():
        day = datetime.strptime(date_str,"%Y-%m-%d").date()
        Metric.objects.create(
            kind=metric_kind,
            start=day,
            end=day + timedelta(days=1),
            value=visits)
