import waffle
from django.core.management.base import BaseCommand

from kitsune.wiki import tasks


class Command(BaseCommand):
    def handle(self, **options):
        # If rebuild on demand switch is on, do nothing.
        if waffle.switch_is_active("wiki-rebuild-on-demand"):
            return

        tasks.rebuild_kb()
