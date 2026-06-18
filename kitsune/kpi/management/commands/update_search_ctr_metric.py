from django.core.management.base import BaseCommand

from kitsune.kpi.tasks import update_search_ctr_metric


class Command(BaseCommand):
    help = "Get new search CTR data from Google Analytics and save."

    def handle(self, **options):
        update_search_ctr_metric()
