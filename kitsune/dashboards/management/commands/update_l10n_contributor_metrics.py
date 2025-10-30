import argparse
from datetime import date

from django.core.management.base import BaseCommand

from kitsune.dashboards.tasks import update_l10n_contributor_metrics


def valid_date(s):
    try:
        return date.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{s}'.")


class Command(BaseCommand):
    help = "Update the number of active contributors for each locale/product."

    def add_arguments(self, parser):
        parser.add_argument("day", nargs="?", type=valid_date)

    def handle(self, day=None, **options):
        """
        An active contributor is defined as a user that created or reviewed a
        revision in the previous calendar month.
        """
        update_l10n_contributor_metrics(day=day)
