from datetime import datetime, date, timedelta

import cronjobs

from dashboards import LAST_90_DAYS
from dashboards.models import WikiDocumentVisits
from kpi.models import (Metric, MetricKind, VISITORS_METRIC_CODE,
                        L10N_METRIC_CODE)
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
        day = datetime.strptime(date_str, '%Y-%m-%d').date()
        Metric.objects.create(
            kind=metric_kind,
            start=day,
            end=day + timedelta(days=1),
            value=visits)


@cronjobs.register
def update_l10n_metric():
    """Calculate new l10n coverage numbers and save."""
    # Get the top 60 visited articles. We will only use the top 50
    # but a handful aren't localizable so we get some extras.
    top_60_qs = WikiDocumentVisits.objects.select_related('document').filter(
        period=LAST_90_DAYS).order_by('-visits')[:50]
    top_60_docs = [v.document for v in top_60_qs]

    # Get the visits to each locale in the last 90 days.
    end = date.today() - timedelta(days=1)  # yesterday
    start = end - timedelta(days=90)
    locale_visits = Webtrends.visits_by_locale(start, end)

    # Discard en-US.
    locale_visits.pop('en-US')

    # Total non en-US visits.
    total_visits = sum(locale_visits.itervalues())

    # Calculate the coverage.
    coverage = 0
    for locale, visits in locale_visits.iteritems():
        up_to_date_docs = 0
        num_docs = 0
        for doc in top_60_docs:
            if num_docs == 50:
                # Stop at 50 documents.
                break

            if not doc.is_localizable:
                # Skip non localizable documents.
                continue

            num_docs += 1
            cur_rev_id = doc.latest_localizable_revision_id
            translation = doc.translated_to(locale)
            if (translation and translation.current_revision_id and
                translation.current_revision_id >= cur_rev_id):
                up_to_date_docs += 1

        coverage += ((float(up_to_date_docs) / num_docs) *
                     (float(visits) / total_visits))

    # Save the value to Metric table.
    metric_kind = MetricKind.objects.get(code=L10N_METRIC_CODE)
    day = date.today()
    Metric.objects.create(
        kind=metric_kind,
        start=day,
        end=day + timedelta(days=1),
        value=int(coverage * 100))  # Store as a % int.
