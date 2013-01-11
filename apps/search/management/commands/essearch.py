from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from search.es_utils import es_search_cmd
from search.utils import FakeLogger


class Command(BaseCommand):
    help = 'Does a front-page search for given query'
    option_list = BaseCommand.option_list + (
        make_option('--pages', type='int', dest='pages', default=1,
                    help='Number of pages of results you want to see'),)

    def handle(self, *args, **options):
        pages = options['pages']
        if not args:
            raise CommandError('You must specify the search query.')

        query = u' '.join(args)

        es_search_cmd(query, pages, FakeLogger(self.stdout))
