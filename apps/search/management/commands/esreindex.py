from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from search.es_utils import es_reindex_cmd


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'
    option_list = BaseCommand.option_list + (
        make_option('--percent', type='int', dest='percent', default=100,
                    help='Reindex a percentage of things'),
        make_option('--delete', action='store_true', dest='delete',
                    help='Wipes index before reindexing'),
        make_option('--models', type='string', dest='models', default=None,
                    help='Comma-separated list of models to index'),
        )

    def handle(self, *args, **options):
        percent = options['percent']
        delete = options['delete']
        models = options['models']
        if models:
            models = models.split(',')
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')
        es_reindex_cmd(percent, delete, models)
