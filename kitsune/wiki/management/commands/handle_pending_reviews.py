from django.core.management.base import BaseCommand
from sentry_sdk import capture_exception

from kitsune.wiki.tasks import handle_pending_reviews


class Command(BaseCommand):
    help = "Handle pending reviews of machine translations in hybrid-strategy locales."

    def handle(self, *args, **options):
        self.stdout.write("Starting to handle pending reviews of machine translations...")
        try:
            task = handle_pending_reviews.delay()
        except Exception as e:
            capture_exception(e)
        else:
            self.stdout.write(self.style.SUCCESS(f"Task queued successfully. Task ID: {task.id}"))
