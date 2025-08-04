from django.core.management.base import BaseCommand
from sentry_sdk import capture_exception

from kitsune.wiki.tasks import handle_due_tasks_for_translations


class Command(BaseCommand):
    help = "Handle due tasks for translations."

    def handle(self, *args, **options):
        self.stdout.write("Starting to handle due tasks for translations...")
        try:
            task = handle_due_tasks_for_translations.delay()
        except Exception as e:
            capture_exception(e)
        else:
            self.stdout.write(self.style.SUCCESS(f"Task queued successfully. Task ID: {task.id}"))
