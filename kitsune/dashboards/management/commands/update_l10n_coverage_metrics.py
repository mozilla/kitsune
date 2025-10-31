from django.core.management.base import BaseCommand

from kitsune.dashboards.tasks import update_l10n_coverage_metrics


class Command(BaseCommand):
    help = "Calculate and store the l10n metrics for each locale/product."

    def handle(self, **options):
        update_l10n_coverage_metrics()
