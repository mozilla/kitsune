from django.core.management.base import BaseCommand, CommandError

from kitsune.search.es_utils import es_search_cmd
from kitsune.search.utils import FakeLogger


class Command(BaseCommand):
    help = 'Does a front-page search for given query'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages', type=int, dest='pages', default=1,
            help='Number of pages of results you want to see')

    def handle(self, *args, **options):
        pages = options['pages']
        if not args:
            raise CommandError('You must specify the search query.')

        query = ' '.join(args)

        es_search_cmd(query, pages, FakeLogger(self.stdout))
