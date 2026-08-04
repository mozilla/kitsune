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
    resolve_active_targets,
)
from kitsune.retrieval.locks import (
    DocumentLockBackendError,
    DocumentLockUnavailable,
    lifecycle_lock,
)
from kitsune.search.es_utils import es_client

# Query-only changes have their own flag because they rewrite `_meta` without a migration.
_MIGRATION_ACTIONS = {
    "reembed": IndexMetaAction.REEMBED,
    "copy": IndexMetaAction.COPY_VECTORS,
}


class Command(BaseCommand):
    help = "Initialize, migrate, and gate the retrieval chunk index and its aliases."

    def add_arguments(self, parser):
        phase = parser.add_mutually_exclusive_group()
        phase.add_argument(
            "--migrate-writes",
            action="store_true",
            help="Create a new stamped generation and point the write alias at it.",
        )
        phase.add_argument(
            "--copy-vectors",
            action="store_true",
            help=(
                "Populate the write generation from the read generation by copying stored "
                "vectors. Makes no provider calls, and is safe to rerun to resume."
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
            help="Rewrite only the query-recipe _meta on active indexes (no corpus work).",
        )
        parser.add_argument(
            "--action",
            choices=sorted(_MIGRATION_ACTIONS),
            help="Required with --migrate-writes: the action you expect to authorize.",
        )

    def handle(self, *args, **options):
        # Fail closed on invalid configuration before touching any index.
        meta = configured_index_meta()
        if options["action"] and not options["migrate_writes"]:
            raise CommandError("--action only applies to --migrate-writes.")

        try:
            with lifecycle_lock() as lease:
                if options["update_query_recipe"]:
                    self._update_query_recipe(meta)
                elif options["migrate_writes"]:
                    self._migrate_writes(meta, options["action"])
                elif options["copy_vectors"]:
                    self._copy_vectors(meta, lease)
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

    def _resume_hint(self, read_index, write_index) -> str:
        """Derive the remaining population step from the generations' stored `_meta`."""
        action = classify_meta_mismatch(read_index_meta(read_index), read_index_meta(write_index))
        if action is IndexMetaAction.COPY_VECTORS:
            return "search_init --copy-vectors"
        return f"sync_chunks --backfill --index {write_index}"

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
                f"Finish it with '{self._resume_hint(read_index, write_index)}', then "
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
        action_name = "copy" if action is IndexMetaAction.COPY_VECTORS else "reembed"
        raise CommandError(
            f"{write_index} requires the authorized '{action.value}' operation before it "
            f"matches the configured recipe/mapping. Run 'search_init --migrate-writes "
            f"--action {action_name}' to authorize it."
        )

    def _migrate_writes(self, meta, action_name):
        if not action_name:
            raise CommandError(
                "--migrate-writes requires --action; name the operation you are authorizing "
                f"({', '.join(sorted(_MIGRATION_ACTIONS))})."
            )

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
                f"'{self._resume_hint(read_index, write_index)}'."
            )

        classified = classify_meta_mismatch(read_index_meta(write_index), meta)
        if classified is not _MIGRATION_ACTIONS[action_name]:
            raise CommandError(
                f"{write_index} differs from the configuration by '{classified.value}', not "
                f"'{action_name}'. Nothing was changed."
            )

        name = create_write_generation(timestamp=datetime.now(tz=UTC), meta=meta)
        emit(
            "retrieval.rebuild.write_migrated",
            source_index=write_index,
            target_index=name,
            action=classified.value,
        )
        next_step = (
            "search_init --copy-vectors"
            if classified is IndexMetaAction.COPY_VECTORS
            else f"sync_chunks --backfill --index {name}"
        )
        self.stdout.write(
            f"Created {name} and moved writes to it. Reads stay on {read_index} "
            f"until the gate passes. Populate it with '{next_step}', then promote it with "
            "'search_init --migrate-reads'."
        )

    def _copy_vectors(self, desired_meta, lease):
        read_index, write_index = self._aliases()
        if not read_index or not write_index or read_index == write_index:
            raise CommandError(
                "A copy needs a diverged pair of aliases. Run 'search_init --migrate-writes "
                "--action copy' first."
            )

        read_meta = read_index_meta(read_index)
        write_meta = read_index_meta(write_index)
        if classify_meta_mismatch(write_meta, desired_meta) is not IndexMetaAction.NONE:
            raise CommandError(
                f"The write generation {write_index} no longer matches the configured "
                "recipe/mapping. Refusing to populate an obsolete target."
            )
        action = classify_meta_mismatch(read_meta, write_meta)
        if action is not IndexMetaAction.COPY_VECTORS:
            raise CommandError(
                f"The migration from {read_index} to {write_index} requires "
                f"'{action.value}', not a vector copy. Nothing was copied."
            )

        # Create-only preserves newer fanned-out writes; their conflicts are expected.
        response = es_client().reindex(
            source={"index": read_index},
            dest={"index": write_index, "op_type": "create"},
            conflicts="proceed",
            wait_for_completion=True,
            refresh=True,
        )
        raw = getattr(response, "body", response)
        total = raw.get("total")
        created = raw.get("created")
        conflicts = raw.get("version_conflicts")
        failures = raw.get("failures")
        counts_valid = all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in (total, created, conflicts)
        )
        if raw.get("timed_out") is not False or failures or not counts_valid:
            raise CommandError(
                f"Copy from {read_index} to {write_index} did not complete cleanly; "
                f"{len(failures or ())} items failed. The generation is incomplete — rerun "
                "'search_init --copy-vectors' to resume."
            )
        if created + conflicts != total:
            raise CommandError(
                f"Copy from {read_index} to {write_index} accounted for {created + conflicts} "
                f"of {total} documents. Rerun 'search_init --copy-vectors' to resume."
            )

        # A slow copy must not report completion after losing lifecycle ownership.
        lease.renew()
        emit(
            "retrieval.rebuild.copy_completed",
            source_index=read_index,
            target_index=write_index,
            documents_created=created,
            version_conflicts=conflicts,
        )
        self.stdout.write(
            f"Copied {created} documents from {read_index} to {write_index}; "
            f"{conflicts} version conflicts left newer writes in place. "
            f"Reconcile with 'sync_chunks --reconcile --index {write_index}', wait for the "
            "workers, then run 'search_init --migrate-reads'."
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
