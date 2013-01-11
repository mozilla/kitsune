from django.core.management.base import BaseCommand, CommandError

from search.es_utils import es_delete_cmd
from search.utils import FakeLogger


class Command(BaseCommand):
    help = 'Delete an index from elastic search.'

    def handle(self, *args, **options):
        if not args:
            raise CommandError('You must specify which index to delete.')

        es_delete_cmd(args[0], FakeLogger(self.stdout))
