from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.kpi.management import utils
from kitsune.kpi.models import (
    SEARCH_CLICKS_METRIC_CODE,
    SEARCH_SEARCHES_METRIC_CODE,
    Metric,
    MetricKind,
)
from kitsune.sumo import googleanalytics


class Command(BaseCommand):
    help = "Get new search CTR data from Google Analytics and save."

    def handle(self, **options):
        if settings.STAGE:
            # Let's be nice to GA and skip on stage.
            return

        # Start updating the day after the last updated.
        latest_metric = utils._get_latest_metric(SEARCH_CLICKS_METRIC_CODE)
        if latest_metric is not None:
            latest_metric_date = latest_metric.start
        else:
            latest_metric_date = date(2011, 1, 1)
        start = latest_metric_date + timedelta(days=1)

        # Collect up until yesterday
        end = date.today() - timedelta(days=1)

        # Get the CTR data from Google Analytics, and create the metrics.
        clicks_kind = MetricKind.objects.get_or_create(code=SEARCH_CLICKS_METRIC_CODE)[0]
        searches_kind = MetricKind.objects.get_or_create(code=SEARCH_SEARCHES_METRIC_CODE)[0]
        for day, num_clicks, num_searches in googleanalytics.search_clicks_and_impressions(
            start, end
        ):
            next_day = day + timedelta(days=1)
            Metric.objects.create(kind=searches_kind, start=day, end=next_day, value=num_searches)
            Metric.objects.create(kind=clicks_kind, start=day, end=next_day, value=num_clicks)
