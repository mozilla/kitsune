from django.core.management.base import BaseCommand
from sentry_sdk import capture_exception

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

        self.stdout.write("Starting to process stale translations...")
        try:
            task = process_stale_translations.delay(limit=limit)
        except Exception as e:
            capture_exception(e)
        else:
            self.stdout.write(self.style.SUCCESS(f"Task queued successfully. Task ID: {task.id}"))
