import logging
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from search.es_utils import es_reindex


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'
    option_list = BaseCommand.option_list + (
        make_option('--percent', type='int', dest='percent', default=100,
                    help='Reindex a percentage of things'),)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        percent = options['percent']
        if percent > 100 or percent < 1:
            raise CommandError('percent should be between 1 and 100')
        es_reindex(percent)
