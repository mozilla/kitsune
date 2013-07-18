from datetime import datetime, date, timedelta

from django.conf import settings
from django.db.models import Count, F

import cronjobs

from kitsune.customercare.models import Reply
from kitsune.dashboards import LAST_90_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.kpi.models import (
    Metric, MetricKind, AOA_CONTRIBUTORS_METRIC_CODE,
    KB_ENUS_CONTRIBUTORS_METRIC_CODE, KB_L10N_CONTRIBUTORS_METRIC_CODE,
    L10N_METRIC_CODE, SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE,
    VISITORS_METRIC_CODE, SEARCH_SEARCHES_METRIC_CODE,
    SEARCH_CLICKS_METRIC_CODE)
from kitsune.kpi.surveygizmo_utils import (
    get_email_addresses, add_email_to_campaign)
from kitsune.questions.models import Answer
from kitsune.sumo import googleanalytics
from kitsune.wiki.config import TYPO_SIGNIFICANCE, MEDIUM_SIGNIFICANCE
from kitsune.wiki.models import Revision


@cronjobs.register
def update_visitors_metric():
    """Get new visitor data from Google Analytics and save."""
    # Start updating the day after the last updated.
    latest_metric = _get_latest_metric(VISITORS_METRIC_CODE)
    if latest_metric is not None:
        latest_metric_date = latest_metric.start
    else:
        latest_metric_date = date(2011, 01, 01)
    start = latest_metric_date + timedelta(days=1)

    # Collect up until yesterday
    end = date.today() - timedelta(days=1)

    # Get the visitor data from Google Analytics.
    visitors = googleanalytics.visitors(start, end)

    # Create the metrics.
    metric_kind = MetricKind.objects.get(code=VISITORS_METRIC_CODE)
    for date_str, visits in visitors.items():
        day = datetime.strptime(date_str, '%Y-%m-%d').date()
        Metric.objects.create(
            kind=metric_kind,
            start=day,
            end=day + timedelta(days=1),
            value=visits)


MAX_DOCS_UP_TO_DATE = 50


@cronjobs.register
def update_l10n_metric():
    """Calculate new l10n coverage numbers and save.

    L10n coverage is a measure of the amount of translations that are
    up to date, weighted by the number of visits for each locale.

    The "algorithm" (see Bug 727084):
    SUMO visits = Total SUMO visits for the last 30 days;
    Total translated = 0;

    For each locale {
        Total up to date = Total up to date +
            ((Number of up to date articles from the en-US top 50 visited)/50 ) *
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
    top_60_docs = _get_top_docs(60)

    # Get the visits to each locale in the last 30 days.
    end = date.today() - timedelta(days=1)  # yesterday
    start = end - timedelta(days=30)
    locale_visits = googleanalytics.visitors_by_locale(start, end)

    # Total visits.
    total_visits = sum(locale_visits.itervalues())

    # Calculate the coverage.
    coverage = 0
    for locale, visits in locale_visits.iteritems():
        if locale == settings.WIKI_DEFAULT_LANGUAGE:
            num_docs = MAX_DOCS_UP_TO_DATE
            up_to_date_docs = MAX_DOCS_UP_TO_DATE
        else:
            up_to_date_docs, num_docs = _get_up_to_date_count(
                top_60_docs, locale)

        if num_docs and total_visits:
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


@cronjobs.register
def update_contributor_metrics(day=None):
    """Calculate and save contributor metrics."""
    update_support_forum_contributors_metric(day)
    update_kb_contributors_metric(day)
    update_aoa_contributors_metric(day)


def update_support_forum_contributors_metric(day=None):
    """Calculate and save the support forum contributor counts.

    An support forum contributor is a user that has replied 10 times
    in the past 30 days to questions that aren't his/her own.
    """
    if day:
        start = end = day
    else:
        latest_metric = _get_latest_metric(
            SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE)
        if latest_metric is not None:
            # Start updating the day after the last updated.
            start = latest_metric.end + timedelta(days=1)
        else:
            start = date(2011, 01, 01)

        # Update until yesterday.
        end = date.today() - timedelta(days=1)

    # Loop through all the days from start to end, calculating and saving.
    day = start
    while day <= end:
        # Figure out the number of contributors from the last 30 days.
        thirty_days_back = day - timedelta(days=30)
        contributors = (Answer.objects
            .exclude(creator=F('question__creator'))
            .filter(
                created__gte=thirty_days_back,
                created__lt=day)
            .values('creator')
            .annotate(count=Count('creator'))
            .filter(count__gte=10))
        count = contributors.count()

        # Save the value to Metric table.
        metric_kind = MetricKind.objects.get(
            code=SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE)
        Metric.objects.create(
            kind=metric_kind,
            start=thirty_days_back,
            end=day,
            value=count)

        day = day + timedelta(days=1)


def update_kb_contributors_metric(day=None):
    """Calculate and save the KB (en-US and L10n) contributor counts.

    A KB contributor is a user that has edited or reviewed a Revision
    in the last 30 days.
    """
    if day:
        start = end = day
    else:
        latest_metric = _get_latest_metric(KB_ENUS_CONTRIBUTORS_METRIC_CODE)
        if latest_metric is not None:
            # Start updating the day after the last updated.
            start = latest_metric.end + timedelta(days=1)
        else:
            start = date(2011, 01, 01)

        # Update until yesterday.
        end = date.today() - timedelta(days=1)

    # Loop through all the days from start to end, calculating and saving.
    day = start
    while day <= end:
        # Figure out the number of contributors from the last 30 days.
        thirty_days_back = day - timedelta(days=30)
        editors = (Revision.objects
            .filter(
                created__gte=thirty_days_back,
                created__lt=day)
            .values_list('creator', flat=True).distinct())
        reviewers = (Revision.objects
            .filter(
                reviewed__gte=thirty_days_back,
                reviewed__lt=day)
            .values_list('reviewer', flat=True).distinct())

        en_us_count = len(set(
            list(editors.filter(document__locale='en-US')) +
            list(reviewers.filter(document__locale='en-US'))
        ))
        l10n_count = len(set(
            list(editors.exclude(document__locale='en-US')) +
            list(reviewers.exclude(document__locale='en-US'))
        ))

        # Save the values to Metric table.
        metric_kind = MetricKind.objects.get(
            code=KB_ENUS_CONTRIBUTORS_METRIC_CODE)
        Metric.objects.create(
            kind=metric_kind,
            start=thirty_days_back,
            end=day,
            value=en_us_count)

        metric_kind = MetricKind.objects.get(
            code=KB_L10N_CONTRIBUTORS_METRIC_CODE)
        Metric.objects.create(
            kind=metric_kind,
            start=thirty_days_back,
            end=day,
            value=l10n_count)

        day = day + timedelta(days=1)


def update_aoa_contributors_metric(day=None):
    """Calculate and save the AoA contributor counts.

    An AoA contributor is a user that has replied in the last 30 days.
    """
    if day:
        start = end = day
    else:
        latest_metric = _get_latest_metric(AOA_CONTRIBUTORS_METRIC_CODE)
        if latest_metric is not None:
            # Start updating the day after the last updated.
            start = latest_metric.end + timedelta(days=1)
        else:
            # Start updating 30 days after the first reply we have.
            try:
                first_reply = Reply.objects.order_by('created')[0]
                start = first_reply.created.date() + timedelta(days=30)
            except IndexError:
                # If there is no data, there is nothing to do here.
                return

        # Update until yesterday.
        end = date.today() - timedelta(days=1)

    # Loop through all the days from start to end, calculating and saving.
    day = start
    while day <= end:
        # Figure out the number of contributors from the last 30 days.
        thirty_days_back = day - timedelta(days=30)
        contributors = (Reply.objects
            .filter(
                created__gte=thirty_days_back,
                created__lt=day)
            .values_list('twitter_username').distinct())
        count = contributors.count()

        # Save the value to Metric table.
        metric_kind = MetricKind.objects.get(code=AOA_CONTRIBUTORS_METRIC_CODE)
        Metric.objects.create(
            kind=metric_kind,
            start=thirty_days_back,
            end=day,
            value=count)

        day = day + timedelta(days=1)


@cronjobs.register
def update_search_ctr_metric():
    """Get new search CTR data from Google Analytics and save."""
    # Start updating the day after the last updated.
    latest_metric = _get_latest_metric(SEARCH_CLICKS_METRIC_CODE)
    if latest_metric is not None:
        latest_metric_date = latest_metric.start
    else:
        latest_metric_date = date(2011, 01, 01)
    start = latest_metric_date + timedelta(days=1)

    # Collect up until yesterday
    end = date.today() - timedelta(days=1)

    # Get the CTR data from Google Analytics.
    ctr_data = googleanalytics.search_ctr(start, end)

    # Create the metrics.
    clicks_kind = MetricKind.objects.get(code=SEARCH_CLICKS_METRIC_CODE)
    searches_kind = MetricKind.objects.get(code=SEARCH_SEARCHES_METRIC_CODE)
    for date_str, ctr in ctr_data.items():
        day = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Note: we've been storing our search data as total number of
        # searches and clicks. Google Analytics only gives us the rate,
        # so I am normalizing to 1000 searches (multiplying the % by 10).
        # I didn't switch everything to a rate because I don't want to
        # throw away the historic data.
        Metric.objects.create(
            kind=searches_kind,
            start=day,
            end=day + timedelta(days=1),
            value=1000)
        Metric.objects.create(
            kind=clicks_kind,
            start=day,
            end=day + timedelta(days=1),
            value=round(ctr, 1) * 10)


def _get_latest_metric(metric_code):
    """Returns the date of the latest metric value."""
    try:
        # Get the latest metric value and return the date.
        last_metric = Metric.objects.filter(
            kind__code=metric_code).order_by('-start')[0]
        return last_metric
    except IndexError:
        return None


def _get_top_docs(count):
    """Get the top documents by visits."""
    top_qs = WikiDocumentVisits.objects.select_related('document').filter(
        period=LAST_90_DAYS).order_by('-visits')[:count]
    return [v.document for v in top_qs]


def _get_up_to_date_count(top_60_docs, locale):
    up_to_date_docs = 0
    num_docs = 0

    for doc in top_60_docs:
        if num_docs == MAX_DOCS_UP_TO_DATE:
            break

        if not doc.is_localizable:
            # Skip non localizable documents.
            continue

        num_docs += 1
        cur_rev_id = doc.latest_localizable_revision_id
        translation = doc.translated_to(locale)

        if not translation or not translation.current_revision_id:
            continue

        if translation.current_revision.based_on_id >= cur_rev_id:
            # The latest translation is based on the latest revision
            # that is ready for localization or a newer one.
            up_to_date_docs += 1
        else:
            # Check if the approved revisions that happened between
            # the last approved translation and the latest revision
            # that is ready for localization are all minor (significance =
            # TYPO_SIGNIFICANCE). If so, the translation is still
            # considered up to date.
            revs = doc.revisions.filter(
                id__gt=translation.current_revision.based_on_id,
                is_approved=True,
                id__lte=cur_rev_id).exclude(significance=TYPO_SIGNIFICANCE)
            if not revs.exists():
                up_to_date_docs += 1
            # If there is only 1 revision of MEDIUM_SIGNIFICANCE, then we
            # count that as half-up-to-date (see bug 790797).
            elif (len(revs) == 1 and
                  revs[0].significance == MEDIUM_SIGNIFICANCE):
                up_to_date_docs += 0.5

    return up_to_date_docs, num_docs


@cronjobs.register
def process_exit_surveys():
    """Exit survey handling.

    * Add new emails collected to the exit survey.
    """

    # Get the email addresses from two days ago and add them to the survey
    # campaign.
    if settings.STAGE:
        # Only run this on prod, it doesn't need to be running multiple times
        # from different places.
        print ('Skipped process_exit_surveys(). '
               'Set settings.STAGE to False to run it for real.')
        return

    startdate = date.today() - timedelta(days=2)
    enddate = date.today() - timedelta(days=1)

    emails = get_email_addresses(startdate, enddate)
    for email in emails:
        add_email_to_campaign(email)

    print '%s emails processed...' % len(emails)
