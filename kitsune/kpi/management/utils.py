import operator
from datetime import date
from datetime import timedelta
from functools import reduce

from django.db.models import Q

from kitsune.dashboards import LAST_90_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.kpi.models import EXIT_SURVEY_DONT_KNOW_CODE
from kitsune.kpi.models import EXIT_SURVEY_NO_CODE
from kitsune.kpi.models import EXIT_SURVEY_YES_CODE
from kitsune.kpi.models import Metric
from kitsune.kpi.models import MetricKind
from kitsune.kpi.surveygizmo_utils import get_exit_survey_results
from kitsune.wiki.config import MEDIUM_SIGNIFICANCE
from kitsune.wiki.config import TYPO_SIGNIFICANCE

MAX_DOCS_UP_TO_DATE = 50


def _get_latest_metric(metric_code):
    """Returns the date of the latest metric value."""
    try:
        # Get the latest metric value and return the date.
        last_metric = Metric.objects.filter(kind__code=metric_code).order_by("-start")[0]
        return last_metric
    except IndexError:
        return None


def _get_top_docs(count):
    """Get the top documents by visits."""
    top_qs = (
        WikiDocumentVisits.objects.select_related("document")
        .filter(period=LAST_90_DAYS)
        .order_by("-visits")[:count]
    )
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
                id__lte=cur_rev_id,
            ).exclude(significance=TYPO_SIGNIFICANCE)
            if not revs.exists():
                up_to_date_docs += 1
            # If there is only 1 revision of MEDIUM_SIGNIFICANCE, then we
            # count that as half-up-to-date (see bug 790797).
            elif len(revs) == 1 and revs[0].significance == MEDIUM_SIGNIFICANCE:
                up_to_date_docs += 0.5

    return up_to_date_docs, num_docs


def _process_exit_survey_results():
    """Collect and save new exit survey results."""
    # Gather and process up until yesterday's exit survey results.
    yes_kind = MetricKind.objects.get_or_create(code=EXIT_SURVEY_YES_CODE)[0]
    no_kind = MetricKind.objects.get_or_create(code=EXIT_SURVEY_NO_CODE)[0]
    dunno_kind = MetricKind.objects.get_or_create(code=EXIT_SURVEY_DONT_KNOW_CODE)[0]

    latest_metric = _get_latest_metric(EXIT_SURVEY_YES_CODE)
    if latest_metric is not None:
        latest_metric_date = latest_metric.start
    else:
        latest_metric_date = date(2013, 7, 1)

    day = latest_metric_date + timedelta(days=1)
    today = date.today()

    while day < today:
        # Get the aggregated results.
        results = get_exit_survey_results("general", day)

        # Store them.
        Metric.objects.create(
            kind=yes_kind, start=day, end=day + timedelta(days=1), value=results["yes"]
        )
        Metric.objects.create(
            kind=no_kind, start=day, end=day + timedelta(days=1), value=results["no"]
        )
        Metric.objects.create(
            kind=dunno_kind, start=day, end=day + timedelta(days=1), value=results["dont-know"]
        )

        # Move on to next day.
        day += timedelta(days=1)


def _count_contributors_in_range(querysets, users, date_range):
    """Of the group ``users``, count how many made a contribution in ``date_range``."""
    start, end = date_range
    retained_users = set()

    for queryset, fields in querysets:
        for field in fields:
            filters = {"%s__in" % field: users, "created__gte": start, "created__lt": end}
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

            first_contrib = queryset.filter(filters).order_by("id")[0]
            return start <= first_contrib.created < end

        cohort |= set(filter(is_in_cohort, potential_users))

    return cohort
