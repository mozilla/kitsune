from django.core.management.base import BaseCommand

from kitsune.sumo.utils import CommandLogger
from kitsune.users.tasks import cleanup_old_account_events


class Command(BaseCommand):
    help = "Deletes account events that are older than two years"

    def handle(self, *args, **options):
        cleanup_old_account_events(logger=CommandLogger(self, options))
