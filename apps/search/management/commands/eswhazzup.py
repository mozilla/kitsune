import logging
from django.core.management.base import BaseCommand
from search.es_utils import es_whazzup_cmd


class Command(BaseCommand):
    help = 'Shows elastic stats.'

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        es_whazzup_cmd()
