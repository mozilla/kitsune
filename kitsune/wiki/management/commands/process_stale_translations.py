from django.core.management.base import BaseCommand

from kitsune.wiki.tasks import process_stale_translations


class Command(BaseCommand):
    help = "Process stale translations using appropriate strategies"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of stale translations to process",
        )

    def handle(self, **options):
        process_stale_translations(limit=options.get("limit"))
