from django.core.management.base import BaseCommand

from search.es_utils import es_reindex


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'

    def handle(self, *args, **options):
        es_reindex()
