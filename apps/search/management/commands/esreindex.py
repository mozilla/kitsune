from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings

from search.es_utils import es_reindex_cmd
from search.utils import FakeLogger


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'
    option_list = BaseCommand.option_list + (
        make_option('--percent', type='int', dest='percent', default=100,
                    help='Reindex a percentage of things'),
        make_option('--delete', action='store_true', dest='delete',
                    help='Wipes index before reindexing'),
        make_option('--mapping_types', type='string', dest='mapping_types',
                    default=None,
                    help='Comma-separated list of mapping types to index'),
        make_option('--criticalmass', action='store_true', dest='criticalmass',
                    help='Indexes a critical mass of things'),
        )

    # We (ab)use override_settings to force ES_LIVE_INDEXING for the
    # duration of this command so that it actually indexes stuff.
    @override_settings(ES_LIVE_INDEXING=True)
    def handle(self, *args, **options):
        percent = options['percent']
        delete = options['delete']
        mapping_types = options['mapping_types']
        criticalmass = options['criticalmass']
        if mapping_types:
            mapping_types = mapping_types.split(',')
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')
        if percent < 100 and criticalmass:
            raise CommandError('you can\'t specify criticalmass and percent')
        if mapping_types and criticalmass:
            raise CommandError(
                'you can\'t specify criticalmass and mapping_types')

        es_reindex_cmd(
            percent=percent,
            delete=delete,
            mapping_types=mapping_types,
            criticalmass=criticalmass,
            log=FakeLogger(self.stdout))
