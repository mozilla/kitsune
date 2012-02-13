import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from search.es_utils import es_reindex_cmd


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'
    option_list = BaseCommand.option_list + (
        make_option('--percent', type='int', dest='percent', default=100,
                    help='Reindex a percentage of things'),)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        percent = options['percent']
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')
        es_reindex_cmd(percent)
