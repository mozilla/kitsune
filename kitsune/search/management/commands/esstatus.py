from django.core.management.base import BaseCommand

from kitsune.search.es_utils import es_status_cmd
from kitsune.search.utils import FakeLogger


class Command(BaseCommand):
    help = "Shows elastic search index status."

    def add_arguments(self, parser):
        parser.add_argument(
            "--checkindex",
            action="store_true",
            dest="checkindex",
            help="Checks the index contents",
        )

    def handle(self, *args, **options):
        es_status_cmd(options["checkindex"], log=FakeLogger(self.stdout))
