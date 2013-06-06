from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from kitsune.search.es_utils import es_delete_cmd
from kitsune.search.utils import FakeLogger


class Command(BaseCommand):
    help = 'Delete an index from elastic search.'
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_true', dest='noinput',
                    help='Do not ask for input--just do it'),
    )

    def handle(self, *args, **options):
        if not args:
            raise CommandError('You must specify which index to delete.')

        es_delete_cmd(
            args[0],
            noinput=options['noinput'],
            log=FakeLogger(self.stdout))
