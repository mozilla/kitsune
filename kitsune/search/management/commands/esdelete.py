from django.core.management.base import BaseCommand, CommandError

from kitsune.search.es_utils import es_delete_cmd
from kitsune.search.utils import FakeLogger


class Command(BaseCommand):
    help = "Delete an index from elastic search."

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            action="store_true",
            dest="noinput",
            help="Do not ask for input--just do it",
        )

    def handle(self, *args, **options):
        if not args:
            raise CommandError("You must specify which index to delete.")

        es_delete_cmd(args[0], noinput=options["noinput"], log=FakeLogger(self.stdout))
