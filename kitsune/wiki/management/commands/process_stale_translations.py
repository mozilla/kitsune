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
        limit = options.get("limit")
        result = process_stale_translations(limit=limit)

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {result['processed_count']} stale translations: "
                f"{result['successful_count']} successful, "
                f"{result['failed_count']} failed, "
                f"{result['queued_count']} queued for async processing"
            )
        )
