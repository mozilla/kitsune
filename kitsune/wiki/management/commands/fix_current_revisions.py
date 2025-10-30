from django.core.management.base import BaseCommand

from kitsune.sumo.utils import CommandLogger
from kitsune.wiki.tasks import fix_current_revisions


class Command(BaseCommand):
    help = "Fixes documents that have the current_revision set incorrectly."

    def handle(self, **options):
        fix_current_revisions(logger=CommandLogger(self, options))
