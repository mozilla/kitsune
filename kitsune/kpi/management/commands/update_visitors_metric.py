from datetime import date, datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.kpi.management.utils import _get_latest_metric
from kitsune.kpi.models import VISITORS_METRIC_CODE, Metric, MetricKind
from kitsune.sumo import googleanalytics


class Command(BaseCommand):
    help = """Get new visitor data from Google Analytics and save."""

    def handle(self, **options):
        if settings.STAGE:
            # Let's be nice to GA and skip on stage.
            return

        # Start updating the day after the last updated.
        latest_metric = _get_latest_metric(VISITORS_METRIC_CODE)
        if latest_metric is not None:
            latest_metric_date = latest_metric.start
        else:
            latest_metric_date = date(2011, 1, 1)
        start = latest_metric_date + timedelta(days=1)

        # Collect up until yesterday
        end = date.today() - timedelta(days=1)

        # Get the visitor data from Google Analytics.
        visitors = googleanalytics.visitors(start, end)

        # Create the metrics.
        metric_kind = MetricKind.objects.get_or_create(code=VISITORS_METRIC_CODE)[0]
        for date_str, visits in list(visitors.items()):
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
            Metric.objects.create(
                kind=metric_kind, start=day, end=day + timedelta(days=1), value=visits
            )
