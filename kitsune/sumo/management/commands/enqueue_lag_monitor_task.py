
from django.core.management.base import BaseCommand
from django.utils import timezone

from kitsune.sumo.tasks import measure_queue_lag


class Command(BaseCommand):
    help = "Fire a task that measures the queue lag."

    def handle(self, **options):
        measure_queue_lag.delay(timezone.now().isoformat())
