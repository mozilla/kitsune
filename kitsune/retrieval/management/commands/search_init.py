from datetime import UTC, datetime

from django.core.management.base import BaseCommand

from kitsune.retrieval.index import ChunkDocument


class Command(BaseCommand):
    help = "Initialize the retrieval chunk index and its read/write aliases."

    def add_arguments(self, parser):
        parser.add_argument(
            "--migrate-writes",
            action="store_true",
            help="Create a new index and point the write alias at it.",
        )
        parser.add_argument(
            "--migrate-reads",
            action="store_true",
            help="Point the read alias at the index the write alias points at.",
        )

    def handle(self, *args, **options):
        migrate_writes = options["migrate_writes"]
        migrate_reads = options["migrate_reads"]

        if not (migrate_writes or migrate_reads):
            index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
            if index:
                self.stdout.write(f"Updating mapping on {index}")
                ChunkDocument.init(index=index)
            else:
                self.stdout.write("First run: creating the index and aliases")
                migrate_writes = migrate_reads = True

        if migrate_writes:
            self.stdout.write("Migrating writes: creating a new index and moving the write alias")
            ChunkDocument.migrate_writes(timestamp=datetime.now(tz=UTC))

        if migrate_reads:
            self.stdout.write("Migrating reads: pointing the read alias at the write index")
            ChunkDocument.migrate_reads()
