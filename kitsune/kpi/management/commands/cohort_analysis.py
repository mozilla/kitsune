from django.core.management.base import BaseCommand

from kitsune.kpi.tasks import cohort_analysis


class Command(BaseCommand):
    def handle(self, **options):
        cohort_analysis()
