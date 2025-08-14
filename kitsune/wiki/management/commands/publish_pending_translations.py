from django.core.management.base import BaseCommand
from sentry_sdk import capture_exception

from kitsune.wiki.tasks import publish_pending_translations


class Command(BaseCommand):
    help = "Publish pending machine translations in hybrid-strategy locales."

    def handle(self, *args, **options):
        self.stdout.write("Starting to publish pending machine translations...")
        try:
            task = publish_pending_translations.delay()
        except Exception as e:
            capture_exception(e)
        else:
            self.stdout.write(self.style.SUCCESS(f"Task queued successfully. Task ID: {task.id}"))
