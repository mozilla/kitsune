from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from search.es_utils import es_reindex_cmd
from search.utils import FakeLogger


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'
    option_list = BaseCommand.option_list + (
        make_option('--percent', type='int', dest='percent', default=100,
                    help='Reindex a percentage of things'),
        make_option('--delete', action='store_true', dest='delete',
                    help='Wipes index before reindexing'),
        make_option('--models', type='string', dest='models', default=None,
                    help='Comma-separated list of models to index'),
        make_option('--criticalmass', action='store_true', dest='criticalmass',
                    help='Indexes a critical mass of things'),
        )

    def handle(self, *args, **options):
        percent = options['percent']
        delete = options['delete']
        models = options['models']
        criticalmass = options['criticalmass']
        if models:
            models = models.split(',')
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')
        if percent < 100 and criticalmass:
            raise CommandError('you can\'t specify criticalmass and percent')
        if models and criticalmass:
            raise CommandError('you can\'t specify criticalmass and models')

        es_reindex_cmd(percent, delete, models, criticalmass,
                       FakeLogger(self.stdout))
