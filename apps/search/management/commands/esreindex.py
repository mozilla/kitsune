import logging
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from search.es_utils import es_reindex
from search.models import get_search_models


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

        if args:
            search_models = get_search_models()
            possible_doctypes = dict((cls._meta.db_table, cls)
                                     for cls in search_models)
            for mem in args:
                if mem not in possible_doctypes:
                    raise CommandError('"%s" is not a valid doctype (%s)' %
                                       (mem, possible_doctypes.keys()))

        # args are the list of doctypes to index.
        es_reindex(args, percent)
