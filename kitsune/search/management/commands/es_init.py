from django.core.management.base import BaseCommand
from elasticsearch_dsl.exceptions import IllegalOperation
from datetime import datetime, timezone

from kitsune.search.es_utils import get_doc_types, es_client


class Command(BaseCommand):
    help = "Initialize ES document types"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=str,
            dest="limit",
            nargs="*",
            default="",
            help="Limit to specific doc types",
        )
        parser.add_argument(
            "--migrate-writes",
            action="store_true",
            help="Create a new index and point the _write alias at it",
        )
        parser.add_argument(
            "--migrate-reads",
            action="store_true",
            help="Update the _read alias to point at the latest index",
        )
        parser.add_argument(
            "--reload-search-analyzers",
            action="store_true",
            help="Reload the search analyzers (used when changing synonyms)",
        )

    def handle(self, *args, **kwargs):
        client = es_client()
        doc_types = get_doc_types()

        limit = kwargs["limit"]
        if limit:
            doc_types = [dt for dt in doc_types if dt.__name__ in limit]

        timestamp = datetime.now(tz=timezone.utc)

        for dt in doc_types:
            print(f"Initializing: {dt.__name__}")

            migrate_writes = kwargs["migrate_writes"]
            migrate_reads = kwargs["migrate_reads"]

            if not (migrate_reads or migrate_writes):
                index = dt.alias_points_at(dt.Index.write_alias)
                if not index:
                    print("First time running, creating index and aliases:")
                    migrate_writes = True
                    migrate_reads = True
                else:
                    print("Updating index")
                    dt.init(index=index)

            if migrate_writes:
                try:
                    print("Migrating writes: creating new index and pointing write alias at it")
                    dt.migrate_writes(timestamp=timestamp)
                except IllegalOperation as e:
                    print(e)

            if migrate_reads:
                try:
                    print("Migrating reads: pointing read alias where write alias points")
                    dt.migrate_reads()
                except IllegalOperation as e:
                    print(e)

            index = dt.alias_points_at(dt.Index.write_alias)
            if kwargs["reload_search_analyzers"]:
                print(f"Reloading search analyzers on {index}")
                client.indices.reload_search_analyzers(index)

            print("")  # print blank line to make console output easier to read
