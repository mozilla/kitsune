import argparse
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models import F

from kitsune.customercare.models import Reply
from kitsune.kpi.management import utils
from kitsune.kpi.models import AOA_CONTRIBUTORS_METRIC_CODE
from kitsune.kpi.models import KB_ENUS_CONTRIBUTORS_METRIC_CODE
from kitsune.kpi.models import KB_L10N_CONTRIBUTORS_METRIC_CODE
from kitsune.kpi.models import Metric
from kitsune.kpi.models import MetricKind
from kitsune.kpi.models import SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE
from kitsune.questions.models import Answer
from kitsune.wiki.models import Revision


def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


class Command(BaseCommand):
    help = "Calculate and save contributor metrics."

    def add_arguments(self, parser):
        parser.add_argument('day', nargs='?', type=valid_date)

    def handle(self, day=None, **options):
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
        Metric.objects.create(
            kind=metric_kind, start=thirty_days_back, end=day, value=count
        )

        day = day + timedelta(days=1)


def update_kb_contributors_metric(day=None):
    """Calculate and save the KB (en-US and L10n) contributor counts.

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
                list(editors.filter(document__locale="en-US")) +
                list(reviewers.filter(document__locale="en-US"))
            )
        )
        l10n_count = len(
            set(
                list(editors.exclude(document__locale="en-US")) +
                list(reviewers.exclude(document__locale="en-US"))
            )
        )

        # Save the values to Metric table.
        metric_kind = MetricKind.objects.get_or_create(code=KB_ENUS_CONTRIBUTORS_METRIC_CODE)[0]
        Metric.objects.create(
            kind=metric_kind, start=thirty_days_back, end=day, value=en_us_count
        )

        metric_kind = MetricKind.objects.get_or_create(code=KB_L10N_CONTRIBUTORS_METRIC_CODE)[0]
        Metric.objects.create(
            kind=metric_kind, start=thirty_days_back, end=day, value=l10n_count
        )

        day = day + timedelta(days=1)


def update_aoa_contributors_metric(day=None):
    """Calculate and save the AoA contributor counts.

    An AoA contributor is a user that has replied in the last 30 days.
    """
    if day:
        start = end = day
    else:
        latest_metric = utils._get_latest_metric(AOA_CONTRIBUTORS_METRIC_CODE)
        if latest_metric is not None:
            # Start updating the day after the last updated.
            start = latest_metric.end + timedelta(days=1)
        else:
            # Start updating 30 days after the first reply we have.
            try:
                first_reply = Reply.objects.order_by("created")[0]
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
            Reply.objects.filter(created__gte=thirty_days_back, created__lt=day)
            .values_list("twitter_username")
            .distinct()
        )
        count = contributors.count()

        # Save the value to Metric table.
        metric_kind = MetricKind.objects.get_or_create(code=AOA_CONTRIBUTORS_METRIC_CODE)[0]
        Metric.objects.create(
            kind=metric_kind, start=thirty_days_back, end=day, value=count
        )

        day = day + timedelta(days=1)
