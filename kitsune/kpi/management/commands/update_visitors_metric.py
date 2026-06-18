from django.core.management.base import BaseCommand

from kitsune.kpi.tasks import update_visitors_metric


class Command(BaseCommand):
    help = """Get new visitor data from Google Analytics and save."""

    def handle(self, **options):
        update_visitors_metric()
