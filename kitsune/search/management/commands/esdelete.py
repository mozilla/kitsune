from django.core.management.base import LabelCommand

from kitsune.search.es_utils import es_delete_cmd
from kitsune.search.utils import FakeLogger


class Command(LabelCommand):
    label = 'index'
    help = 'Delete an index from elastic search.'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--noinput', action='store_true', dest='noinput',
            help='Do not ask for input--just do it')

    def handle_label(self, label, **options):
        es_delete_cmd(
            label,
            noinput=options['noinput'],
            log=FakeLogger(self.stdout))
