from datetime import date
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.kpi.management import utils
from kitsune.kpi.models import L10N_METRIC_CODE
from kitsune.kpi.models import Metric
from kitsune.kpi.models import MetricKind
from kitsune.sumo import googleanalytics


class Command(BaseCommand):
    help = "Calculate new l10n coverage numbers and save."

    def handle(self, **options):
        """
        L10n coverage is a measure of the amount of translations that are
        up to date, weighted by the number of visits for each locale.

        The "algorithm" (see Bug 727084):
        SUMO visits = Total SUMO visits for the last 30 days;
        Total translated = 0;

        For each locale {
            Total up to date = Total up to date +
                ((Number of up to date articles in the en-US top 50 visited)/50 ) *
                (Visitors for that locale / SUMO visits));
        }

        An up to date article is any of the following:
        * An en-US article (by definition it is always up to date)
        * The latest en-US revision has been translated
        * There are only new revisions with TYPO_SIGNIFICANCE not translated
        * There is only one revision of MEDIUM_SIGNIFICANCE not translated
        """
        # Get the top 60 visited articles. We will only use the top 50
        # but a handful aren't localizable so we get some extras.
        top_60_docs = utils._get_top_docs(60)

        # Get the visits to each locale in the last 30 days.
        end = date.today() - timedelta(days=1)  # yesterday
        start = end - timedelta(days=30)
        locale_visits = googleanalytics.visitors_by_locale(start, end)

        # Total visits.
        total_visits = sum(locale_visits.values())

        # Calculate the coverage.
        coverage = 0
        for locale, visits in locale_visits.items():
            if locale == settings.WIKI_DEFAULT_LANGUAGE:
                num_docs = utils.MAX_DOCS_UP_TO_DATE
                up_to_date_docs = utils.MAX_DOCS_UP_TO_DATE
            else:
                up_to_date_docs, num_docs = utils._get_up_to_date_count(top_60_docs, locale)

            if num_docs and total_visits:
                coverage += (float(up_to_date_docs) / num_docs) * (float(visits) / total_visits)

        # Save the value to Metric table.
        metric_kind = MetricKind.objects.get_or_create(code=L10N_METRIC_CODE)[0]
        day = date.today()
        Metric.objects.create(
            kind=metric_kind, start=day, end=day + timedelta(days=1), value=int(coverage * 100),
        )  # Store as a % int.
