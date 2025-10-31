from django.core.management.base import BaseCommand

from kitsune.sumo.utils import CommandLogger
from kitsune.wiki.tasks import run_rebuild_kb


class Command(BaseCommand):
    def handle(self, **options):
        run_rebuild_kb(logger=CommandLogger(self, options))
