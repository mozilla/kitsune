from django.core.management.base import BaseCommand

from kitsune.wiki.tasks import create_missing_translations


class Command(BaseCommand):
    help = "Create missing translations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of missing translations to create",
        )

    def handle(self, **options):
        create_missing_translations(limit=options.get("limit"))
