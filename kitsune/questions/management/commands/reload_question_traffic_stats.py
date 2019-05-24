from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.questions.models import QuestionVisits


class Command(BaseCommand):
    help = "Reload question views from the analytics."

    def handle(self, **options):
        QuestionVisits.reload_from_analytics(verbose=settings.DEBUG)
