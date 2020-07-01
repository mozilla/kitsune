from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.dashboards.models import PERIODS
from kitsune.dashboards.models import WikiDocumentVisits


class Command(BaseCommand):
    def handle(self, **options):
        for period, _ in PERIODS:
            WikiDocumentVisits.reload_period_from_analytics(period, verbose=settings.DEBUG)
