import json
import operator
from datetime import datetime, date, timedelta
from functools import reduce

from django.conf import settings
from django.db.models import Count, F, Q

import cronjobs
import requests
from statsd import statsd

from kitsune.customercare.models import Reply
from kitsune.dashboards import LAST_90_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.kpi.models import (
    Metric, MetricKind, CohortKind, Cohort, RetentionMetric, AOA_CONTRIBUTORS_METRIC_CODE,
    KB_ENUS_CONTRIBUTORS_METRIC_CODE, KB_L10N_CONTRIBUTORS_METRIC_CODE, L10N_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE, VISITORS_METRIC_CODE, SEARCH_SEARCHES_METRIC_CODE,
    SEARCH_CLICKS_METRIC_CODE, EXIT_SURVEY_YES_CODE, EXIT_SURVEY_NO_CODE,
    EXIT_SURVEY_DONT_KNOW_CODE, CONTRIBUTOR_COHORT_CODE, KB_ENUS_CONTRIBUTOR_COHORT_CODE,
    KB_L10N_CONTRIBUTOR_COHORT_CODE, SUPPORT_FORUM_HELPER_COHORT_CODE, AOA_CONTRIBUTOR_COHORT_CODE,
    CONTRIBUTORS_CSAT_METRIC_CODE, AOA_CONTRIBUTORS_CSAT_METRIC_CODE,
    KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE, KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE)
from kitsune.kpi.surveygizmo_utils import (
    get_email_addresses, add_email_to_campaign, get_exit_survey_results,
    SURVEYS)
from kitsune.questions.models import Answer, Question
from kitsune.sumo import googleanalytics
from kitsune.wiki.config import TYPO_SIGNIFICANCE, MEDIUM_SIGNIFICANCE
from kitsune.wiki.models import Revision


@cronjobs.register
def update_visitors_metric():
    """Get new visitor data from Google Analytics and save."""
    if settings.STAGE:
        # Let's be nice to GA and skip on stage.
        return

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
            ((Number of up to date articles in the en-US top 50 visited)/50 ) *
             (Visitors for that locale / SUMO visits));
    }

    An up to date article is any of the following:
    * An en-US article (by definition it is always up to date)
    * The latest en-US revision has been translated
    * There are only new revisions with TYPO_SIGNIFICANCE not translated
    * There is only one revision of MEDIUM_SIGNIFICANCE not translated
    """
    if settings.STAGE:
        # Let's be nice to GA and skip on stage.
        return

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
    if settings.STAGE:
        # Let's be nice to the admin node and skip on stage.
        return

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
        contributors = (
            Answer.objects.exclude(creator=F('question__creator'))
            .filter(created__gte=thirty_days_back,
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
        editors = (
            Revision.objects.filter(
                created__gte=thirty_days_back,
                created__lt=day)
            .values_list('creator', flat=True).distinct())
        reviewers = (
            Revision.objects.filter(
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
        contributors = (
            Reply.objects.filter(
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
    if settings.STAGE:
        # Let's be nice to GA and skip on stage.
        return

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

    * Collect new exit survey results.
    * Save results to our metrics table.
    * Add new emails collected to the exit survey.
    """

    _process_exit_survey_results()

    # Get the email addresses from two days ago and add them to the survey
    # campaign (skip this on stage).
    if settings.STAGE:
        # Only run this on prod, it doesn't need to be running multiple times
        # from different places.
        return

    startdate = date.today() - timedelta(days=2)
    enddate = date.today() - timedelta(days=1)

    for survey in SURVEYS.keys():
        if 'email_collection_survey_id' not in SURVEYS[survey]:
            # Some surveys don't have email collection on the site
            # (the askers survey, for example).
            continue

        emails = get_email_addresses(survey, startdate, enddate)
        for email in emails:
            add_email_to_campaign(survey, email)

        statsd.gauge('survey.{0}'.format(survey), len(emails))


def _process_exit_survey_results():
    """Collect and save new exit survey results."""
    # Gather and process up until yesterday's exit survey results.
    yes_kind, _ = MetricKind.objects.get_or_create(code=EXIT_SURVEY_YES_CODE)
    no_kind, _ = MetricKind.objects.get_or_create(code=EXIT_SURVEY_NO_CODE)
    dunno_kind, _ = MetricKind.objects.get_or_create(
        code=EXIT_SURVEY_DONT_KNOW_CODE)

    latest_metric = _get_latest_metric(EXIT_SURVEY_YES_CODE)
    if latest_metric is not None:
        latest_metric_date = latest_metric.start
    else:
        latest_metric_date = date(2013, 07, 01)

    day = latest_metric_date + timedelta(days=1)
    today = date.today()

    while day < today:
        # Get the aggregated results.
        results = get_exit_survey_results('general', day)

        # Store them.
        Metric.objects.create(
            kind=yes_kind,
            start=day,
            end=day + timedelta(days=1),
            value=results['yes'])
        Metric.objects.create(
            kind=no_kind,
            start=day,
            end=day + timedelta(days=1),
            value=results['no'])
        Metric.objects.create(
            kind=dunno_kind,
            start=day,
            end=day + timedelta(days=1),
            value=results['dont-know'])

        # Move on to next day.
        day += timedelta(days=1)


@cronjobs.register
def survey_recent_askers():
    """Add question askers to a surveygizmo campaign to get surveyed."""
    if settings.STAGE:
        # Only run this on prod, it doesn't need to be running multiple times
        # from different places.
        return

    # We get the email addresses of all users that asked a question 2 days
    # ago. Then, all we have to do is send the email address to surveygizmo
    # and it does the rest.
    two_days_ago = date.today() - timedelta(days=2)
    yesterday = date.today() - timedelta(days=1)

    emails = (
        Question.objects
        .filter(created__gte=two_days_ago, created__lt=yesterday)
        .values_list('creator__email', flat=True))
    for email in emails:
            add_email_to_campaign('askers', email)

    statsd.gauge('survey.askers', len(emails))


@cronjobs.register
def cohort_analysis():
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    boundaries = [today - timedelta(days=today.weekday())]
    for _ in range(12):
        previous_week = boundaries[-1] - timedelta(weeks=1)
        boundaries.append(previous_week)
    boundaries.reverse()
    ranges = zip(boundaries[:-1], boundaries[1:])

    reports = [
        (CONTRIBUTOR_COHORT_CODE, [
            (Revision.objects.all(), ('creator', 'reviewer',)),
            (Answer.objects.not_by_asker(), ('creator',)),
            (Reply.objects.all(), ('user',))]),
        (KB_ENUS_CONTRIBUTOR_COHORT_CODE, [
            (Revision.objects.filter(document__locale='en-US'), ('creator', 'reviewer',))]),
        (KB_L10N_CONTRIBUTOR_COHORT_CODE, [
            (Revision.objects.exclude(document__locale='en-US'), ('creator', 'reviewer',))]),
        (SUPPORT_FORUM_HELPER_COHORT_CODE, [
            (Answer.objects.not_by_asker(), ('creator',))]),
        (AOA_CONTRIBUTOR_COHORT_CODE, [
            (Reply.objects.all(), ('user',))])
    ]

    for kind, querysets in reports:
        cohort_kind, _ = CohortKind.objects.get_or_create(code=kind)

        for i, cohort_range in enumerate(ranges):
            cohort_users = _get_cohort(querysets, cohort_range)

            # Sometimes None will be added to the cohort_users list, so remove it
            if None in cohort_users:
                cohort_users.remove(None)

            cohort, _ = Cohort.objects.update_or_create(
                kind=cohort_kind, start=cohort_range[0], end=cohort_range[1],
                defaults={'size': len(cohort_users)})

            for retention_range in ranges[i:]:
                retained_user_count = _count_contributors_in_range(querysets, cohort_users,
                                                                   retention_range)
                RetentionMetric.objects.update_or_create(
                    cohort=cohort, start=retention_range[0], end=retention_range[1],
                    defaults={'size': retained_user_count})


def _count_contributors_in_range(querysets, users, date_range):
    """Of the group ``users``, count how many made a contribution in ``date_range``."""
    start, end = date_range
    retained_users = set()

    for queryset, fields in querysets:
        for field in fields:
            filters = {'%s__in' % field: users, 'created__gte': start, 'created__lt': end}
            retained_users |= set(getattr(o, field) for o in queryset.filter(**filters))

    return len(retained_users)


def _get_cohort(querysets, date_range):
    start, end = date_range
    cohort = set()

    for queryset, fields in querysets:
        contributions_in_range = queryset.filter(created__gte=start, created__lt=end)
        potential_users = set()

        for field in fields:
            potential_users |= set(getattr(cont, field) for cont in contributions_in_range)

        def is_in_cohort(u):
            qs = [Q(**{field: u}) for field in fields]
            filters = reduce(operator.or_, qs)

            first_contrib = queryset.filter(filters).order_by('id')[0]
            return start <= first_contrib.created < end

        cohort |= set(filter(is_in_cohort, potential_users))

    return cohort


@cronjobs.register
def calculate_csat_metrics():
    user = settings.SURVEYGIZMO_USER
    password = settings.SURVEYGIZMO_PASSWORD
    startdate = date.today() - timedelta(days=2)
    enddate = date.today() - timedelta(days=1)
    page = 1
    more_pages = True
    survey_id = SURVEYS['general']['community_health']

    csat = {
        CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        AOA_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
    }

    counts = {
        CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        AOA_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
        KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE: 0,
    }

    while more_pages:
        response = requests.get(
            'https://restapi.surveygizmo.com/v2/survey/{survey}'
            '/surveyresponse?'
            'filter[field][0]=datesubmitted'
            '&filter[operator][0]=>=&filter[value][0]={start}+0:0:0'
            '&filter[field][1]=datesubmitted'
            '&filter[operator][1]=<&filter[value][1]={end}+0:0:0'
            '&filter[field][2]=status&filter[operator][2]=='
            '&filter[value][2]=Complete'
            '&resultsperpage=500'
            '&page={page}'
            '&user:pass={user}:{password}'.format(
                survey=survey_id, start=startdate,
                end=enddate, page=page, user=user, password=password),
            timeout=300)

        results = json.loads(response.content)
        total_pages = results.get('total_pages', 1)
        more_pages = page < total_pages

        if 'data' in results:
            for r in results['data']:
                try:
                    rating = int(r['[question(3)]'])
                except ValueError:
                    # CSAT question was not answered
                    pass
                else:
                    csat[CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                    counts[CONTRIBUTORS_CSAT_METRIC_CODE] += 1

                    if len(r['[question(4), option(10010)]']):  # Army of Awesome
                        csat[AOA_CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                        counts[AOA_CONTRIBUTORS_CSAT_METRIC_CODE] += 1

                    if len(r['[question(4), option(10011)]']):  # Support Forum
                        csat[SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                        counts[SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE] += 1

                    if len(r['[question(4), option(10012)]']):  # KB EN-US
                        csat[KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                        counts[KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE] += 1

                    if len(r['[question(4), option(10013)]']):  # KB L10N
                        csat[KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE] += rating
                        counts[KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE] += 1

        page += 1

    for code in csat:
        metric_kind, _ = MetricKind.objects.get_or_create(code=code)
        value = csat[code] / counts[code] if counts[code] else 50  # If no responses assume neutral
        Metric.objects.update_or_create(kind=metric_kind, start=startdate, end=enddate,
                                        defaults={'value': value})


@cronjobs.register
def csat_survey_emails():
    querysets = [(Revision.objects.all(), ('creator', 'reviewer',)),
                 (Answer.objects.not_by_asker(), ('creator',)),
                 (Reply.objects.all(), ('user',))]

    end = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=30)

    users = _get_cohort(querysets, (start, end))

    for u in users:
        p = u.profile
        if p.csat_email_sent is None or p.csat_email_sent < start:
            survey_id = SURVEYS['general']['community_health']
            campaign_id = SURVEYS['general']['community_health_campaign_id']

            try:
                requests.put(
                    'https://restapi.surveygizmo.com/v4/survey/{survey}/surveycampaign/'
                    '{campaign}/contact?semailaddress={email}&api_token={token}'
                    '&api_token_secret={secret}&allowdupe=true'.format(
                        survey=survey_id, campaign=campaign_id, email=u.email,
                        token=settings.SURVEYGIZMO_API_TOKEN,
                        secret=settings.SURVEYGIZMO_API_TOKEN_SECRET),
                    timeout=30)
            except requests.exceptions.Timeout:
                print 'Timed out adding: %s' % u.email
            else:
                p.csat_email_sent = datetime.now()
                p.save()
