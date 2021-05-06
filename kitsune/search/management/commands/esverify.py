from django.core.management.base import BaseCommand

from kitsune.search.es_utils import es_verify_cmd
from kitsune.search.utils import FakeLogger


class Command(BaseCommand):
    help = "Verifies correctness of all things verifyable."

    def handle(self, *args, **options):
        es_verify_cmd(FakeLogger(self.stdout))
