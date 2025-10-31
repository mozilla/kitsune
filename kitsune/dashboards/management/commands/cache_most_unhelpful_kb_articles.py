from django.core.management.base import BaseCommand

from kitsune.dashboards.tasks import cache_most_unhelpful_kb_articles


class Command(BaseCommand):
    help = "Calculate and save the most unhelpful KB articles in the past two weeks."

    def handle(self, **options):
        cache_most_unhelpful_kb_articles()
