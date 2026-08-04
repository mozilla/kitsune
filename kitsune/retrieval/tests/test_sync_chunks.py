from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from kitsune.retrieval.gate import GateCategory
from kitsune.retrieval.index import ChunkDocument, ChunkIdentity
from kitsune.retrieval.sync import sync_document_chunks
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.users.tests import GroupFactory
from kitsune.wiki.models import Document
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

COMMAND = "kitsune.retrieval.management.commands.sync_chunks"


class ModeSelectionTests(SimpleTestCase):
    """Exactly one mode, chosen explicitly — the command never guesses what to do."""

    def test_a_mode_is_required(self):
        with self.assertRaises(CommandError):
            call_command("sync_chunks")

    def test_page_size_must_be_positive(self):
        with self.assertRaises(CommandError):
            call_command("sync_chunks", "--backfill", "--page-size", "0")

    def test_modes_are_mutually_exclusive(self):
        for pair in (
            ("--backfill", "--reconcile"),
            ("--backfill", "--gate"),
            ("--reconcile", "--gate"),
        ):
            with self.subTest(pair=pair), self.assertRaises(CommandError):
                call_command("sync_chunks", *pair)


@override_settings(RETRIEVAL_INGESTION_ENABLED=False)
class IngestionDisabledTests(SimpleTestCase):
    """Enqueueing modes refuse to run rather than reporting success without queueing."""

    def test_enqueueing_modes_refuse_to_run(self):
        for mode in ("--backfill", "--reconcile"):
            with self.subTest(mode=mode):
                with self.assertRaisesMessage(CommandError, "Retrieval ingestion is disabled"):
                    call_command("sync_chunks", mode)

    def test_the_refusal_precedes_any_elasticsearch_work(self):
        # No index is named and no alias is resolved, so a refusal that reached
        # resolve_active_targets would need a live cluster this test does not have.
        with mock.patch(f"{COMMAND}.resolve_active_targets") as targets:
            with self.assertRaises(CommandError):
                call_command("sync_chunks", "--backfill")
        targets.assert_not_called()

    def test_reporting_modes_are_unaffected(self):
        # --dry-run and --gate queue nothing, so they stay usable before the pipeline is on:
        # both get past the refusal and on to resolving targets.
        for args in (("--backfill", "--dry-run"), ("--gate",)):
            with self.subTest(args=args):
                with mock.patch(f"{COMMAND}.resolve_active_targets", return_value=()) as targets:
                    with self.assertRaisesMessage(CommandError, "No active retrieval index"):
                        call_command("sync_chunks", *args)
                targets.assert_called_once()


@override_settings(RETRIEVAL_INGESTION_ENABLED=True)
class SyncChunksTestCase(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        self.document = self._document("Install Firefox", "install-firefox")
        self.identity = ChunkIdentity("kb", str(self.document.id), self.document.locale)

    def _document(self, title, slug):
        document = DocumentFactory(title=title, slug=slug)
        ApprovedRevisionFactory(document=document, summary=f"{title} summary")
        document.refresh_from_db()
        return document

    def _run(self, *args, **options):
        out = StringIO()
        call_command("sync_chunks", *args, stdout=out, stderr=out, **options)
        return out.getvalue()


class BackfillTests(SyncChunksTestCase):
    def test_every_eligible_document_is_enqueued_pinned_to_the_active_targets(self):
        second = self._document("Sync bookmarks", "sync-bookmarks")

        with mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue:
            self._run("--backfill")

        enqueue.assert_called_once_with([self.document.id, second.id], target_indexes=[self.index])

    def test_an_explicit_index_pins_only_that_generation(self):
        with mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue:
            self._run("--backfill", "--index", self.index)

        self.assertEqual(enqueue.call_args.kwargs["target_indexes"], [self.index])

    def test_an_alias_is_rejected_where_a_concrete_index_is_required(self):
        with self.assertRaises(CommandError):
            self._run("--backfill", "--index", ChunkDocument.Index.write_alias)

    def test_backfill_enumeration_is_bounded_by_page_size(self):
        second = self._document("Sync bookmarks", "sync-bookmarks")

        with mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue:
            self._run("--backfill", "--page-size", "1")

        self.assertEqual(
            enqueue.call_args_list,
            [
                mock.call([self.document.id], target_indexes=[self.index]),
                mock.call([second.id], target_indexes=[self.index]),
            ],
        )

    def test_an_ineligible_document_is_never_enqueued(self):
        restricted = self._document("Internal runbook", "internal-runbook")
        restricted.restrict_to_groups.add(GroupFactory())

        with mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue:
            self._run("--backfill")

        self.assertEqual(enqueue.call_args.args[0], [self.document.id])

    def test_a_locale_filter_narrows_the_backfill(self):
        translation = DocumentFactory(
            parent=self.document, locale="de", title="Installieren", slug="de-installieren"
        )
        ApprovedRevisionFactory(document=translation)

        with mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue:
            self._run("--backfill", "--locale", "de")

        self.assertEqual(enqueue.call_args.args[0], [translation.id])

    def test_a_dry_run_reports_the_count_without_enqueueing(self):
        with mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue:
            output = self._run("--backfill", "--dry-run")

        enqueue.assert_not_called()
        self.assertIn("would enqueue 1 ", output)
        self.assertIn("dry run", output.lower())

    def test_no_active_target_is_an_error_rather_than_a_silent_no_op(self):
        with mock.patch(f"{COMMAND}.resolve_active_targets", return_value=()):
            with self.assertRaises(CommandError):
                self._run("--backfill")


class ReconcileTests(SyncChunksTestCase):
    def test_a_stale_document_is_enqueued_pinned_to_the_index_that_is_stale(self):
        with (
            mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue,
            mock.patch(f"{COMMAND}.enqueue_document_delete") as evict,
        ):
            self._run("--reconcile")

        enqueue.assert_called_once_with([self.document.id], target_indexes=[self.index])
        evict.assert_not_called()

    def test_an_identity_with_no_eligible_document_is_enqueued_for_deletion(self):
        sync_document_chunks(self.document.id)
        Document.objects.filter(pk=self.document.id).delete()

        with (
            mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue,
            mock.patch(f"{COMMAND}.enqueue_document_delete") as evict,
        ):
            self._run("--reconcile")

        evict.assert_called_once_with(self.identity, target_indexes=[self.index])
        enqueue.assert_not_called()

    def test_a_clean_index_dispatches_nothing(self):
        sync_document_chunks(self.document.id)

        with (
            mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue,
            mock.patch(f"{COMMAND}.enqueue_document_delete") as evict,
        ):
            output = self._run("--reconcile")

        enqueue.assert_not_called()
        evict.assert_not_called()
        self.assertIn("clean", output.lower())

    def test_access_drift_is_reported_prominently_and_without_group_identifiers(self):
        sync_document_chunks(self.document.id)
        # A distinctive id and name: a small integer would match a count or part of the
        # timestamped index name by coincidence, so asserting its absence would prove nothing.
        group = GroupFactory(id=987_654_321, name="Confidential Partner Staff")
        self.document.restrict_to_groups.add(group)

        with (
            mock.patch(f"{COMMAND}.enqueue_document_batch"),
            mock.patch(f"{COMMAND}.enqueue_document_delete") as evict,
        ):
            output = self._run("--reconcile")

        self.assertIn("ACCESS DRIFT", output.upper())
        self.assertIn(GateCategory.ACCESS_DRIFT.value, output)
        self.assertNotIn(str(group.id), output)
        self.assertNotIn(group.name, output)
        evict.assert_called_once_with(self.identity, target_indexes=[self.index])

    def test_a_dry_run_dispatches_nothing(self):
        with (
            mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue,
            mock.patch(f"{COMMAND}.enqueue_document_delete") as evict,
        ):
            output = self._run("--reconcile", "--dry-run")

        enqueue.assert_not_called()
        evict.assert_not_called()
        self.assertIn("dry run", output.lower())

    def test_the_command_does_not_claim_the_queue_is_drained(self):
        with mock.patch(f"{COMMAND}.enqueue_document_batch"):
            output = self._run("--reconcile")

        self.assertIn("--gate", output)


class GateModeTests(SyncChunksTestCase):
    def test_a_clean_index_passes_and_reports_what_it_checked(self):
        sync_document_chunks(self.document.id)

        output = self._run("--gate")

        self.assertIn("clean", output.lower())
        self.assertIn(self.index, output)

    def test_a_dirty_index_fails_and_names_the_categories(self):
        with self.assertRaises(CommandError) as caught:
            self._run("--gate")

        self.assertIn(GateCategory.MISSING_DOCUMENT.value, str(caught.exception))

    def test_the_gate_mode_repairs_nothing(self):
        with (
            mock.patch(f"{COMMAND}.enqueue_document_batch") as enqueue,
            mock.patch(f"{COMMAND}.enqueue_document_delete") as evict,
            self.assertRaises(CommandError),
        ):
            self._run("--gate")

        enqueue.assert_not_called()
        evict.assert_not_called()

    def test_a_dirty_index_still_reports_before_failing(self):
        sync_document_chunks(self.document.id)
        missing = self._document("Sync bookmarks", "sync-bookmarks")
        out = StringIO()

        with self.assertRaises(CommandError):
            call_command("sync_chunks", "--gate", stdout=out, stderr=out)

        self.assertIn(GateCategory.MISSING_DOCUMENT.value, out.getvalue())
        self.assertIn(f"kb:{missing.id}:en-US", out.getvalue())
