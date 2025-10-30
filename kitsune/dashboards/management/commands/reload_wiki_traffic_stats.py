from django.core.management.base import BaseCommand

from kitsune.dashboards.tasks import reload_wiki_traffic_stats


class Command(BaseCommand):
    def handle(self, **options):
        reload_wiki_traffic_stats(verbose=options.get("verbosity", 1) >= 1)
