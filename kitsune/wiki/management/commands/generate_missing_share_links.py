from django.core.management.base import BaseCommand

from kitsune.sumo.utils import CommandLogger
from kitsune.wiki.tasks import generate_missing_share_links


class Command(BaseCommand):
    help = "Generate share links for documents without them."

    def handle(self, **options):
        generate_missing_share_links(logger=CommandLogger(self, options))
