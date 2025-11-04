from datetime import date, datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import Count, F

from kitsune.kpi.management import utils
from kitsune.kpi.models import (
    CONTRIBUTOR_COHORT_CODE,
    KB_ENUS_CONTRIBUTOR_COHORT_CODE,
    KB_ENUS_CONTRIBUTORS_METRIC_CODE,
    KB_L10N_CONTRIBUTOR_COHORT_CODE,
    KB_L10N_CONTRIBUTORS_METRIC_CODE,
    L10N_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE,
    SUPPORT_FORUM_HELPER_COHORT_CODE,
    Cohort,
    CohortKind,
    Metric,
    MetricKind,
    RetentionMetric,
)
from kitsune.questions.models import Answer
from kitsune.sumo import googleanalytics
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.wiki.models import Revision


def update_support_forum_contributors_metric(day: date | None = None) -> None:
    """
    Calculate and save the support forum contributor counts.

    An support forum contributor is a user that has replied 10 times
    in the past 30 days to questions that aren't his/her own.
    """
    if day:
        start = end = day
    else:
        latest_metric = utils._get_latest_metric(SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE)
        if latest_metric is not None:
            # Start updating the day after the last updated.
            start = latest_metric.end + timedelta(days=1)
        else:
            start = date(2011, 1, 1)

        # Update until yesterday.
        end = date.today() - timedelta(days=1)

    # Loop through all the days from start to end, calculating and saving.
    day = start
    while day <= end:
        # Figure out the number of contributors from the last 30 days.
        thirty_days_back = day - timedelta(days=30)
        contributors = (
            Answer.objects.exclude(creator=F("question__creator"))
            .filter(created__gte=thirty_days_back, created__lt=day)
            .values("creator")
            .annotate(count=Count("creator"))
            .filter(count__gte=10)
        )
        count = contributors.count()

        # Save the value to Metric table.
        metric_kind = MetricKind.objects.get_or_create(
            code=SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE
        )[0]
        Metric.objects.create(kind=metric_kind, start=thirty_days_back, end=day, value=count)

        day = day + timedelta(days=1)


def update_kb_contributors_metric(day: date | None = None) -> None:
    """
    Calculate and save the KB (en-US and L10n) contributor counts.

    A KB contributor is a user that has edited or reviewed a Revision
    in the last 30 days.
    """
    if day:
        start = end = day
    else:
        latest_metric = utils._get_latest_metric(KB_ENUS_CONTRIBUTORS_METRIC_CODE)
        if latest_metric is not None:
            # Start updating the day after the last updated.
            start = latest_metric.end + timedelta(days=1)
        else:
            start = date(2011, 1, 1)

        # Update until yesterday.
        end = date.today() - timedelta(days=1)

    # Loop through all the days from start to end, calculating and saving.
    day = start
    while day <= end:
        # Figure out the number of contributors from the last 30 days.
        thirty_days_back = day - timedelta(days=30)
        editors = (
            Revision.objects.filter(created__gte=thirty_days_back, created__lt=day)
            .values_list("creator", flat=True)
            .distinct()
        )
        reviewers = (
            Revision.objects.filter(reviewed__gte=thirty_days_back, reviewed__lt=day)
            .values_list("reviewer", flat=True)
            .distinct()
        )

        en_us_count = len(
            set(
                list(editors.filter(document__locale="en-US"))
                + list(reviewers.filter(document__locale="en-US"))
            )
        )
        l10n_count = len(
            set(
                list(editors.exclude(document__locale="en-US"))
                + list(reviewers.exclude(document__locale="en-US"))
            )
        )

        # Save the values to Metric table.
        metric_kind = MetricKind.objects.get_or_create(code=KB_ENUS_CONTRIBUTORS_METRIC_CODE)[0]
        Metric.objects.create(kind=metric_kind, start=thirty_days_back, end=day, value=en_us_count)

        metric_kind = MetricKind.objects.get_or_create(code=KB_L10N_CONTRIBUTORS_METRIC_CODE)[0]
        Metric.objects.create(kind=metric_kind, start=thirty_days_back, end=day, value=l10n_count)

        day = day + timedelta(days=1)


@shared_task
@skip_if_read_only_mode
def update_contributor_metrics(day_isoformat: str | None = None) -> None:
    day = date.today() if day_isoformat is None else date.fromisoformat(day_isoformat)
    update_support_forum_contributors_metric(day)
    update_kb_contributors_metric(day)


@shared_task
@skip_if_read_only_mode
def update_l10n_metric() -> None:
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
        kind=metric_kind,
        start=day,
        end=day + timedelta(days=1),
        value=int(coverage * 100),
    )  # Store as a % int.


@shared_task
@skip_if_read_only_mode
def cohort_analysis() -> None:
    """Groups users into cohorts."""
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    boundaries = [today - timedelta(days=today.weekday())]
    for _ in range(12):
        previous_week = boundaries[-1] - timedelta(weeks=1)
        boundaries.append(previous_week)
    boundaries.reverse()
    ranges = list(zip(boundaries[:-1], boundaries[1:], strict=False))

    reports = [
        (
            CONTRIBUTOR_COHORT_CODE,
            [
                (Revision.objects.all(), ("creator", "reviewer")),
                (Answer.objects.not_by_asker(), ("creator",)),
            ],
        ),
        (
            KB_ENUS_CONTRIBUTOR_COHORT_CODE,
            [(Revision.objects.filter(document__locale="en-US"), ("creator", "reviewer"))],
        ),
        (
            KB_L10N_CONTRIBUTOR_COHORT_CODE,
            [(Revision.objects.exclude(document__locale="en-US"), ("creator", "reviewer"))],
        ),
        (
            SUPPORT_FORUM_HELPER_COHORT_CODE,
            [(Answer.objects.not_by_asker(), ("creator",))],
        ),
    ]

    for kind, querysets in reports:
        cohort_kind, _ = CohortKind.objects.get_or_create(code=kind)

        for i, cohort_range in enumerate(ranges):
            cohort_users = utils._get_cohort(querysets, cohort_range)

            # Sometimes None will be added to the cohort_users list, so remove it
            if None in cohort_users:
                cohort_users.remove(None)

            cohort, _ = Cohort.objects.update_or_create(
                kind=cohort_kind,
                start=cohort_range[0],
                end=cohort_range[1],
                defaults={"size": len(cohort_users)},
            )

            for retention_range in ranges[i:]:
                retained_user_count = utils._count_contributors_in_range(
                    querysets, cohort_users, retention_range
                )
                RetentionMetric.objects.update_or_create(
                    cohort=cohort,
                    start=retention_range[0],
                    end=retention_range[1],
                    defaults={"size": retained_user_count},
                )
