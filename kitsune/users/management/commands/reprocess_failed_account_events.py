from django.core.management.base import BaseCommand

from kitsune.users.tasks import process_unprocessed_account_events


class Command(BaseCommand):
    help = "Process all unprocessed account events created within the given number of hours."

    def add_arguments(self, parser):
        parser.add_argument(
            "--within-hours",
            type=int,
            default=24,
            help=(
                "The number of hours within which the unprocessed "
                "account events have been created."
            ),
        )

    def handle(self, *args, **options):
        process_unprocessed_account_events.delay(options["within_hours"])
