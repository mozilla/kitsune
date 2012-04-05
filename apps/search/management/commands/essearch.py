import logging

from django.core.management.base import BaseCommand, CommandError

from search.es_utils import es_search_cmd


class Command(BaseCommand):
    help = 'Does a front-page search for given query'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        if not args:
            raise CommandError('You must specify the search query.')

        query = u' '.join(args)

        es_search_cmd(query)
