from django.core.management.base import BaseCommand

from kitsune.questions.tasks import update_weekly_votes
from kitsune.sumo.utils import CommandLogger


class Command(BaseCommand):
    help = "Keep the num_votes_past_week value accurate."

    def handle(self, **options):
        update_weekly_votes(logger=CommandLogger(self, options))
