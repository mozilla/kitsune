from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings

from kitsune.search.es_utils import es_reindex_cmd
from kitsune.search.utils import FakeLogger


class Command(BaseCommand):
    help = "Reindex the database for Elastic."

    def add_arguments(self, parser):
        parser.add_argument(
            "--percent",
            type=int,
            dest="percent",
            default=100,
            help="Reindex a percentage of things",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            dest="delete",
            help="Wipes index before reindexing",
        )
        parser.add_argument(
            "--hours-ago",
            type=int,
            dest="hours_ago",
            default=0,
            help="Reindex things updated N hours ago",
        )
        parser.add_argument(
            "--minutes-ago",
            type=int,
            dest="minutes_ago",
            default=0,
            help="Reindex things updated N minutes ago",
        )
        parser.add_argument(
            "--seconds-ago",
            type=int,
            dest="seconds_ago",
            default=0,
            help="Reindex things updated N seconds ago",
        )
        parser.add_argument(
            "--mapping_types",
            dest="mapping_types",
            default=None,
            help="Comma-separated list of mapping types to index",
        )
        parser.add_argument(
            "--criticalmass",
            action="store_true",
            dest="criticalmass",
            help="Indexes a critical mass of things",
        )

    # We (ab)use override_settings to force ES_LIVE_INDEXING for the
    # duration of this command so that it actually indexes stuff.
    @override_settings(ES_LIVE_INDEXING=True)
    def handle(self, *args, **options):
        percent = options["percent"]
        delete = options["delete"]
        mapping_types = options["mapping_types"]
        criticalmass = options["criticalmass"]
        seconds_ago = options["seconds_ago"]
        seconds_ago += options["minutes_ago"] * 60
        seconds_ago += options["hours_ago"] * 3600
        if mapping_types:
            mapping_types = mapping_types.split(",")
        if not 1 <= percent <= 100:
            raise CommandError("percent should be between 1 and 100")
        if percent < 100 and seconds_ago:
            raise CommandError("you can't specify a time ago and percent")
        if criticalmass and seconds_ago:
            raise CommandError("you can't specify a time ago and criticalmass")
        if percent < 100 and criticalmass:
            raise CommandError("you can't specify criticalmass and percent")
        if mapping_types and criticalmass:
            raise CommandError("you can't specify criticalmass and mapping_types")

        es_reindex_cmd(
            percent=percent,
            delete=delete,
            mapping_types=mapping_types,
            criticalmass=criticalmass,
            seconds_ago=seconds_ago,
            log=FakeLogger(self.stdout),
        )
