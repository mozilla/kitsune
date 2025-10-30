from django.core.management.base import BaseCommand

from kitsune.questions.tasks import reload_question_traffic_stats


class Command(BaseCommand):
    help = "Reload question pageviews from the Google Analytics."

    def handle(self, **options):
        reload_question_traffic_stats(verbose=options.get("verbosity", 1) >= 1)
