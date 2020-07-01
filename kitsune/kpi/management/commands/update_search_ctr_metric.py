from datetime import date
from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.kpi.management import utils
from kitsune.kpi.models import Metric
from kitsune.kpi.models import MetricKind
from kitsune.kpi.models import SEARCH_CLICKS_METRIC_CODE
from kitsune.kpi.models import SEARCH_SEARCHES_METRIC_CODE
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

        # Get the CTR data from Google Analytics.
        ctr_data = googleanalytics.search_ctr(start, end)

        # Create the metrics.
        clicks_kind = MetricKind.objects.get_or_create(code=SEARCH_CLICKS_METRIC_CODE)[0]
        searches_kind = MetricKind.objects.get_or_create(code=SEARCH_SEARCHES_METRIC_CODE)[0]
        for date_str, ctr in list(ctr_data.items()):
            day = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Note: we've been storing our search data as total number of
            # searches and clicks. Google Analytics only gives us the rate,
            # so I am normalizing to 1000 searches (multiplying the % by 10).
            # I didn't switch everything to a rate because I don't want to
            # throw away the historic data.
            Metric.objects.create(
                kind=searches_kind, start=day, end=day + timedelta(days=1), value=1000
            )
            Metric.objects.create(
                kind=clicks_kind, start=day, end=day + timedelta(days=1), value=round(ctr, 1) * 10,
            )
