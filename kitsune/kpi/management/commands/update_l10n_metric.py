from django.core.management.base import BaseCommand

from kitsune.kpi.tasks import update_l10n_metric


class Command(BaseCommand):
    help = "Calculate new l10n coverage numbers and save."

    def handle(self, **options):
        update_l10n_metric()
