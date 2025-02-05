from django.core.management.base import BaseCommand

from kitsune.users.tasks import process_unprocessed_account_events


class Command(BaseCommand):
    help = "Process all unprocessed account events created within the given past number of days."

    def add_arguments(self, parser):
        parser.add_argument(
            "num_days_ago",
            type=int,
            help=(
                "The past number of days within which the "
                "unprocessed account events have been created."
            ),
        )

    def handle(self, *args, **options):
        process_unprocessed_account_events.delay(options["num_days_ago"])
