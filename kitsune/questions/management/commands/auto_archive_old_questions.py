from django.core.management.base import BaseCommand

from kitsune.questions.tasks import auto_archive_old_questions
from kitsune.sumo.utils import CommandLogger


class Command(BaseCommand):
    help = "Archive all questions that were created over 180 days ago."

    def handle(self, **options):
        auto_archive_old_questions(logger=CommandLogger(self, options))
