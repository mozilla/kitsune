from django.core.management.base import BaseCommand

from kitsune.search.es_utils import es_mappings_are_correct


class Command(BaseCommand):
    help = 'Checks if mappings are correct.'

    def handle(self, *args, **options):
        results = es_mappings_are_correct()

        for index, result in results:
            print '{0:<20} {1}'.format(index, 'Good' if result else 'Bad')
