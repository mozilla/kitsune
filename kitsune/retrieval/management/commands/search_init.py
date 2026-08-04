"""Safely manage retrieval index generations and their read/write aliases.

A bare invocation only classifies. Generation creation requires explicit cost authorization,
and read promotion requires a clean integrity gate.

Lifecycle decisions re-read aliases under a lease; long phases prove ownership again before
completion. Commands neither drain Celery nor delete the previous read generation used for
rollback.
"""

from datetime import UTC, datetime

from django.core.management.base import BaseCommand, CommandError

from kitsune.retrieval.events import emit
from kitsune.retrieval.fingerprints import (
    IndexMetaAction,
    classify_meta_mismatch,
    read_index_meta,
    write_index_meta,
)
from kitsune.retrieval.gate import gate_index
from kitsune.retrieval.index import (
    ChunkDocument,
    configured_index_meta,
    create_write_generation,
)
from kitsune.retrieval.locks import (
    DocumentLockBackendError,
    DocumentLockUnavailable,
    lifecycle_lock,
)


class Command(BaseCommand):
    help = "Initialize, migrate, and gate the retrieval chunk index and its aliases."

    def add_arguments(self, parser):
        phase = parser.add_mutually_exclusive_group()
        phase.add_argument(
            "--start-rebuild",
            action="store_true",
            help=(
                "Authorize a paid full rebuild: create a stamped generation and move the "
                "write alias to it."
            ),
        )
        phase.add_argument(
            "--migrate-reads",
            action="store_true",
            help="Run the integrity gate against the write generation and, if clean, serve it.",
        )
        phase.add_argument(
            "--update-query-recipe",
            action="store_true",
            help="Rewrite only query-recipe _meta on the stable generation (no corpus work).",
        )

    def handle(self, *args, **options):
        # Fail closed on invalid configuration before touching any index.
        meta = configured_index_meta()

        try:
            with lifecycle_lock() as lease:
                if options["update_query_recipe"]:
                    self._update_query_recipe(meta)
                elif options["start_rebuild"]:
                    self._start_rebuild(meta)
                elif options["migrate_reads"]:
                    self._migrate_reads(meta, lease)
                else:
                    self._classify_or_initialize(meta)
        except DocumentLockUnavailable as exc:
            raise CommandError(
                "Another retrieval lifecycle operation is in progress; nothing was changed."
            ) from exc
        except DocumentLockBackendError as exc:
            raise CommandError(
                "The lock backend is unreachable, so lifecycle changes cannot be serialized."
            ) from exc

    def _aliases(self):
        """Read alias state under the current lifecycle lease."""
        return (
            ChunkDocument.alias_points_at(ChunkDocument.Index.read_alias),
            ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias),
        )

    def _classify_or_initialize(self, meta):
        read_index, write_index = self._aliases()
        if not write_index:
            name = create_write_generation(timestamp=datetime.now(tz=UTC), meta=meta)
            emit("retrieval.rebuild.write_initialized", index=name)
            self.stdout.write(
                f"First run: created {name}. It is intentionally not yet a read target — "
                f"backfill it with 'sync_chunks --backfill --index {name}', then promote it "
                "with 'search_init --migrate-reads'."
            )
            return

        if read_index != write_index:
            if not read_index:
                self.stdout.write(
                    f"First-run population is in flight on {write_index}. Backfill it with "
                    f"'sync_chunks --backfill --index {write_index}', then promote it with "
                    "'search_init --migrate-reads'."
                )
                return
            self.stdout.write(
                f"A migration is in flight: reads on {read_index}, writes on {write_index}. "
                f"Finish it with 'sync_chunks --backfill --index {write_index}', then "
                "'search_init --migrate-reads'."
            )
            return

        action = classify_meta_mismatch(read_index_meta(write_index), meta)
        if action is IndexMetaAction.NONE:
            self.stdout.write(
                f"Configuration matches; updating mapping in place on {write_index}."
            )
            ChunkDocument.init(index=write_index)
            return
        if action is IndexMetaAction.QUERY_META_UPDATE:
            raise CommandError(
                f"{write_index} requires a query-recipe metadata update. Run "
                "'search_init --update-query-recipe'; no corpus rebuild is required."
            )
        raise CommandError(
            f"{write_index} requires a paid full rebuild before it matches the configured "
            "recipe/mapping. Run 'search_init --start-rebuild' to authorize it."
        )

    def _start_rebuild(self, meta):
        read_index, write_index = self._aliases()
        if not write_index:
            raise CommandError("There is no generation to migrate from. Run 'search_init' first.")
        if read_index != write_index:
            if not read_index:
                raise CommandError(
                    f"First-run population is already in flight on {write_index}. Refusing "
                    "to create another generation before it is promoted."
                )
            raise CommandError(
                f"A migration is already in flight: reads on {read_index}, writes on "
                f"{write_index}. Refusing to create a third generation — finish this one with "
                f"'sync_chunks --backfill --index {write_index}'."
            )

        classified = classify_meta_mismatch(read_index_meta(write_index), meta)
        if classified is not IndexMetaAction.REBUILD:
            raise CommandError(
                f"{write_index} does not require a full rebuild; classified action is "
                f"'{classified.value}'. Nothing was changed."
            )

        name = create_write_generation(timestamp=datetime.now(tz=UTC), meta=meta)
        emit(
            "retrieval.rebuild.write_migrated",
            source_index=write_index,
            target_index=name,
        )
        self.stdout.write(
            f"Created {name} and moved writes to it. Reads stay on {read_index} "
            f"until the gate passes. Populate it with 'sync_chunks --backfill --index {name}', "
            "then promote it with 'search_init --migrate-reads'."
        )

    def _migrate_reads(self, desired_meta, lease):
        read_index, write_index = self._aliases()
        if not write_index:
            raise CommandError("There is no write generation to promote. Run 'search_init' first.")
        mismatch = classify_meta_mismatch(read_index_meta(write_index), desired_meta)
        if mismatch is not IndexMetaAction.NONE:
            raise CommandError(
                f"The write generation {write_index} no longer matches the configured "
                f"recipe/mapping ('{mismatch.value}'). Refusing to promote it."
            )
        if read_index == write_index:
            self.stdout.write(f"Reads already serve {write_index}; nothing to promote.")
            return

        report = gate_index(write_index)
        if not report.is_clean:
            raise CommandError(
                f"Integrity gate failed for {write_index} ({', '.join(sorted(report.counts))}); "
                f"reads still serve {read_index or 'nothing'}. Repair it with "
                f"'sync_chunks --reconcile --index {write_index}' and rerun."
            )

        # The gate can be slow. Prove ownership again immediately before moving the alias.
        lease.renew()
        ChunkDocument.migrate_reads()
        emit(
            "retrieval.rebuild.read_migrated",
            source_index=read_index,
            target_index=write_index,
        )
        self.stdout.write(
            f"Reads now serve {write_index}. {read_index or 'No previous generation'} is "
            "retained for rollback and will not be deleted automatically."
        )

    def _update_query_recipe(self, meta):
        read_index, write_index = self._aliases()
        if not write_index:
            self.stdout.write("No retrieval index; nothing to update.")
            return
        if read_index != write_index:
            raise CommandError(
                "Query-recipe updates require a stable read/write generation; finish the "
                "current first-run or rebuild workflow first."
            )

        current = read_index_meta(write_index)
        action = classify_meta_mismatch(current, meta)
        if action is IndexMetaAction.NONE:
            self.stdout.write(f"{write_index}: query recipe already current.")
            return
        if action is not IndexMetaAction.QUERY_META_UPDATE:
            raise CommandError(
                f"{write_index} differs by '{action.value}', not a query-only change; "
                "refusing to rewrite _meta."
            )

        write_index_meta(write_index, {**current, "query": dict(meta["query"])})
        self.stdout.write(f"{write_index}: updated query-recipe _meta.")
