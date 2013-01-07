import time
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from search.es_utils import es_reindex_cmd


class FakeLogger(object):
    """Fake logger that we can pretend is a Python Logger

    Why? Well, because Django has logging settings that prevent me
    from setting up a logger here that uses the stdout that the Django
    BaseCommand has. At some point p while fiddling with it, I
    figured, 'screw it--I'll just write my own' and did.

    The minor ramification is that this isn't a complete
    implementation so if it's missing stuff, we'll have to add it.
    """

    def __init__(self, stdout):
        self.stdout = stdout

    def _out(self, level, *args):
        if len(args) > 0:
            args = args[0] % args[1:]
        else:
            args = args[0]
        self.stdout.write('%s %-8s: %s\n' % (
                time.strftime('%H:%M:%S'), level, args))

    def info(self, *args):
        self._out('INFO', *args)

    def error(self, *args):
        self._out('ERROR', *args)


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'
    option_list = BaseCommand.option_list + (
        make_option('--percent', type='int', dest='percent', default=100,
                    help='Reindex a percentage of things'),
        make_option('--delete', action='store_true', dest='delete',
                    help='Wipes index before reindexing'),
        make_option('--models', type='string', dest='models', default=None,
                    help='Comma-separated list of models to index'),
        make_option('--criticalmass', action='store_true', dest='criticalmass',
                    help='Indexes a critical mass of things'),
        )

    def handle(self, *args, **options):
        percent = options['percent']
        delete = options['delete']
        models = options['models']
        criticalmass = options['criticalmass']
        if models:
            models = models.split(',')
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')
        if percent < 100 and criticalmass:
            raise CommandError('you can\'t specify criticalmass and percent')
        if models and criticalmass:
            raise CommandError('you can\'t specify criticalmass and models')

        es_reindex_cmd(percent, delete, models, criticalmass,
                       FakeLogger(self.stdout))
