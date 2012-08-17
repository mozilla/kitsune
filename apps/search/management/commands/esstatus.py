from optparse import make_option

from django.core.management.base import BaseCommand

from search.es_utils import es_status_cmd


class Command(BaseCommand):
    help = 'Shows elastic search index status.'
    option_list = BaseCommand.option_list + (
        make_option('--checkindex', action='store_true', dest='checkindex',
                    help='Checks the index contents'),)

    def handle(self, *args, **options):
        checkindex = options['checkindex']
        es_status_cmd(checkindex)
