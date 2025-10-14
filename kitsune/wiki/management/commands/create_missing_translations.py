from django.core.management.base import BaseCommand
from sentry_sdk import capture_exception

from kitsune.wiki.tasks import create_missing_translations


class Command(BaseCommand):
    help = "Create missing translations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of missing translations to create",
        )

    def handle(self, **options):
        limit = options.get("limit")

        self.stdout.write("Starting to create missing translations...")
        try:
            task = create_missing_translations.delay(limit=limit)
        except Exception as e:
            capture_exception(e)
        else:
            self.stdout.write(self.style.SUCCESS(f"Task queued successfully. Task ID: {task.id}"))
