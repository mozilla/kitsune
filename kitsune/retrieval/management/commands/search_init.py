from datetime import UTC, datetime

from django.core.management.base import BaseCommand, CommandError

from kitsune.retrieval.fingerprints import (
    IndexMetaAction,
    classify_meta_mismatch,
    read_index_meta,
    write_index_meta,
)
from kitsune.retrieval.index import (
    ChunkDocument,
    configured_index_meta,
    create_write_generation,
    resolve_active_targets,
)


class Command(BaseCommand):
    help = "Initialize and gate the retrieval chunk index and its read/write aliases."

    def add_arguments(self, parser):
        parser.add_argument(
            "--migrate-writes",
            action="store_true",
            help="Create a new stamped index and point the write alias at it.",
        )
        parser.add_argument(
            "--migrate-reads",
            action="store_true",
            help=(
                "Reserved for integrity-gated read promotion; disabled until the gate "
                "orchestration is implemented."
            ),
        )
        parser.add_argument(
            "--update-query-recipe",
            action="store_true",
            help="Rewrite only the query-recipe _meta on active indexes (no corpus work).",
        )

    def handle(self, *args, **options):
        # Fail closed on invalid configuration before touching any index.
        meta = configured_index_meta()
        migrate_writes = options["migrate_writes"]
        migrate_reads = options["migrate_reads"]
        update_query_recipe = options["update_query_recipe"]

        if update_query_recipe and (migrate_writes or migrate_reads):
            raise CommandError(
                "--update-query-recipe cannot be combined with index migration options."
            )

        if migrate_reads:
            raise CommandError(
                "Read migration is disabled until the retrieval integrity gate is implemented; "
                "no aliases were changed."
            )

        if update_query_recipe:
            self._update_query_recipe(meta)
            return

        if not migrate_writes:
            self._gate_or_initialize(meta)
            return

        name = create_write_generation(timestamp=datetime.now(tz=UTC), meta=meta)
        self.stdout.write(f"Migrated writes to {name}.")

    def _gate_or_initialize(self, meta):
        write_index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        if not write_index:
            name = create_write_generation(timestamp=datetime.now(tz=UTC), meta=meta)
            self.stdout.write(
                f"First run: created {name}. It is intentionally not yet a read target — "
                "backfill and run the integrity gate; read promotion remains disabled until "
                "that gate is wired into search_init."
            )
            return

        action = classify_meta_mismatch(read_index_meta(write_index), meta)
        if action is IndexMetaAction.NONE:
            self.stdout.write(
                f"Configuration matches; updating mapping in place on {write_index}."
            )
            ChunkDocument.init(index=write_index)
            return
        raise CommandError(
            f"{write_index} requires the authorized '{action.value}' operation before it "
            "matches the configured recipe/mapping; search_init will not perform it implicitly."
        )

    def _update_query_recipe(self, meta):
        targets = resolve_active_targets()
        if not targets:
            self.stdout.write("No active retrieval indexes; nothing to update.")
            return

        updates = []
        for target in targets:
            current = read_index_meta(target)
            action = classify_meta_mismatch(current, meta)
            if action is IndexMetaAction.NONE:
                self.stdout.write(f"{target}: query recipe already current.")
            elif action is IndexMetaAction.QUERY_META_UPDATE:
                updates.append((target, {**current, "query": dict(meta["query"])}))
            else:
                raise CommandError(
                    f"{target} differs by '{action.value}', not a query-only change; refusing "
                    "to rewrite _meta."
                )

        # Preflight every active target before mutating any of them. Elasticsearch cannot make
        # mapping updates across indexes transactional, but a predictable incompatibility must
        # never leave an earlier target partially updated.
        for target, updated_meta in updates:
            write_index_meta(target, updated_meta)
            self.stdout.write(f"{target}: updated query-recipe _meta.")
