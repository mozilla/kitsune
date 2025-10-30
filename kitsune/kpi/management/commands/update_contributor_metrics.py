import argparse
from datetime import date

from django.core.management.base import BaseCommand

from kitsune.kpi.tasks import update_contributor_metrics


def valid_date(s):
    try:
        return date.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Not a valid date: '{s}'.")


class Command(BaseCommand):
    help = "Calculate and save contributor metrics."

    def add_arguments(self, parser):
        parser.add_argument("day", nargs="?", type=valid_date)

    def handle(self, day=None, **options):
        update_contributor_metrics(day=day)
