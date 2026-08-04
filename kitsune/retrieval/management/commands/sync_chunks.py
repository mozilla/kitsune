"""Backfill, reconcile, or gate the retrieval chunk index.

The three modes are mutually exclusive and one must be named: this command can spend provider
money and can delete indexed content, so it never infers what an operator meant. Reconciliation
dispatches from the integrity gate's own findings rather than a second opinion about what
"stale" means — the gate is what guards a read swap, so the two must not be able to disagree.

Work is enqueued, not performed. Like ``es_reindex``, the command does not claim the queue has
drained; an operator reruns ``--gate`` once the workers are done.
"""

from itertools import batched

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from elasticsearch import NotFoundError

from kitsune.retrieval.eligibility import eligible_documents
from kitsune.retrieval.embeddings import InvalidEmbeddingRecipe
from kitsune.retrieval.fingerprints import InvalidIndexMeta
from kitsune.retrieval.gate import DEFAULT_PAGE_SIZE, GateCategory, gate_index
from kitsune.retrieval.index import (
    InvalidDocumentState,
    recipe_for_index,
    resolve_active_targets,
)
from kitsune.retrieval.tasks import enqueue_document_batch, enqueue_document_delete

# Reported on its own line, above the ordinary counts: a stale access set is the one finding
# that changes who can reach the content.
_PROMINENT = GateCategory.ACCESS_DRIFT


class Command(BaseCommand):
    help = "Backfill, reconcile, or gate the retrieval chunk index."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument(
            "--backfill",
            action="store_true",
            help="Enqueue every eligible document, pinned to the selected target(s).",
        )
        mode.add_argument(
            "--reconcile",
            action="store_true",
            help="Gate, then enqueue repairs and evictions for what the gate found.",
        )
        mode.add_argument(
            "--gate",
            action="store_true",
            help="Report integrity only. Writes nothing and enqueues nothing.",
        )
        parser.add_argument(
            "--index",
            action="append",
            default=None,
            metavar="NAME",
            help=(
                "Concrete index to act on; repeatable. Absent means one snapshot of the "
                "currently active read and write targets."
            ),
        )
        parser.add_argument(
            "--locale",
            action="append",
            default=None,
            metavar="LOCALE",
            help="Restrict to these locales; repeatable. Absent means every locale.",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=DEFAULT_PAGE_SIZE,
            help="Rows fetched from the database per page while enumerating.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be enqueued without dispatching anything.",
        )

    def handle(self, *args, **options):
        page_size = options["page_size"]
        if page_size <= 0:
            raise CommandError("--page-size must be a positive integer.")

        # Refuse rather than no-op: a backfill that reports success without queueing anything
        # is worse than one that fails. --gate and --dry-run only report, so they stay usable
        # for inspecting an index before the pipeline is turned on.
        #
        # --gate is the only mode that never enqueues, and --dry-run suppresses dispatch in the
        # other two. Written as "not gate" so a mode added later is guarded until it opts out.
        would_enqueue = not options["gate"] and not options["dry_run"]
        if would_enqueue and not settings.RETRIEVAL_INGESTION_ENABLED:
            raise CommandError(
                "Retrieval ingestion is disabled, which turns off queueing. "
                "Set RETRIEVAL_INGESTION_ENABLED to enable it, or add --dry-run to report only."
            )

        selected_targets = options["index"] or resolve_active_targets()
        targets = list(dict.fromkeys(selected_targets))
        if not targets:
            raise CommandError(
                "No active retrieval index. Run search_init first, or name one with --index."
            )
        try:
            for target in targets:
                recipe_for_index(target)
        except (
            InvalidDocumentState,
            InvalidEmbeddingRecipe,
            InvalidIndexMeta,
            NotFoundError,
        ) as exc:
            raise CommandError(str(exc)) from exc

        locales = list(dict.fromkeys(options["locale"] or ()))
        if any(not locale for locale in locales):
            raise CommandError("--locale must not be empty.")
        dry_run = options["dry_run"]

        if options["backfill"]:
            self._backfill(targets, locales, page_size, dry_run)
        elif options["reconcile"]:
            self._reconcile(targets, locales, page_size, dry_run)
        else:
            self._gate(targets, locales, page_size)

    def _backfill(self, targets, locales, page_size, dry_run):
        documents = eligible_documents()
        if locales:
            documents = documents.filter(locale__in=locales)
        document_ids = (
            documents.order_by("pk").values_list("id", flat=True).iterator(chunk_size=page_size)
        )
        count = 0
        for ids in batched(document_ids, page_size, strict=False):
            count += len(ids)
            if not dry_run:
                enqueue_document_batch(list(ids), target_indexes=targets)

        if dry_run:
            self.stdout.write(
                f"dry run: would enqueue {count} documents for {', '.join(targets)}."
            )
            return
        self.stdout.write(
            f"Enqueued {count} documents for {', '.join(targets)}. "
            "Rerun with --gate once the workers have drained."
        )

    def _reconcile(self, targets, locales, page_size, dry_run):
        dispatched = False
        for index in targets:
            report = gate_index(index, locales=locales, page_size=page_size)
            self._report(report)
            if report.is_clean:
                continue

            verb = "would enqueue" if dry_run else "Enqueued"
            if report.stale_document_ids:
                dispatched = True
                if not dry_run:
                    enqueue_document_batch(list(report.stale_document_ids), target_indexes=[index])
                self.stdout.write(
                    f"{index}: {verb} {len(report.stale_document_ids)} documents for re-sync."
                )
            if report.unexpected_identities:
                dispatched = True
                if not dry_run:
                    for identity in report.unexpected_identities:
                        enqueue_document_delete(identity, target_indexes=[index])
                self.stdout.write(
                    f"{index}: {verb} {len(report.unexpected_identities)} evictions."
                )
        if dry_run:
            self.stdout.write("dry run: nothing was enqueued.")
        elif dispatched:
            self.stdout.write("Rerun with --gate once the workers have drained.")

    def _gate(self, targets, locales, page_size):
        dirty = []
        for index in targets:
            report = gate_index(index, locales=locales, page_size=page_size)
            self._report(report)
            if not report.is_clean:
                dirty.append(f"{index} ({', '.join(sorted(report.counts))})")
        if dirty:
            raise CommandError(f"Integrity gate failed for {'; '.join(dirty)}.")

    def _report(self, report):
        """One index's counts and bounded findings, without sensitive payloads."""
        self.stdout.write(
            f"{report.index}: checked {report.documents_checked} eligible documents against "
            f"{report.identities_indexed} indexed identities."
        )
        if report.is_clean:
            self.stdout.write(f"{report.index}: clean.")
            return

        if drift := report.counts.get(_PROMINENT.value):
            self.stdout.write(
                self.style.ERROR(
                    f"{report.index}: ACCESS DRIFT — {drift} identities "
                    f"({_PROMINENT.value}) do not match the database's access set."
                )
            )
        for category, count in sorted(report.counts.items()):
            if category != _PROMINENT.value:
                self.stdout.write(f"{report.index}: {count} {category}.")
        for finding in report.findings:
            identity = finding.identity
            detail = f": {finding.detail}" if finding.detail else ""
            self.stdout.write(
                f"{report.index}: {finding.category.value} for "
                f"{identity.content_type}:{identity.object_id}:{identity.locale}{detail}."
            )
        if report.findings_omitted:
            self.stdout.write(
                f"{report.index}: {report.findings_omitted} further findings not listed; "
                "the counts above are complete."
            )
