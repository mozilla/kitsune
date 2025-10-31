from django.core.management.base import BaseCommand

from kitsune.questions.tasks import cleanup_old_spam
from kitsune.sumo.utils import CommandLogger


class Command(BaseCommand):
    help = "Clean up old spam Questions and Answers."

    def handle(self, **options):
        cleanup_old_spam(logger=CommandLogger(self, options))
