from django.core.management.base import BaseCommand

from kitsune.users.tasks import process_unprocessed_account_events


class Command(BaseCommand):
    help = "Process unprocessed account events."

    def handle(self, **options):
        process_unprocessed_account_events.delay()
