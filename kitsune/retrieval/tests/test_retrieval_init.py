from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError

from kitsune.retrieval.chunking import CHUNKING_GENERATION
from kitsune.retrieval.embeddings import configured_embedding_recipe
from kitsune.retrieval.fingerprints import (
    IndexMetaAction,
    InvalidIndexMeta,
    build_index_meta,
    classify_meta_mismatch,
    read_index_meta,
    write_index_meta,
)
from kitsune.retrieval.index import (
    SCHEMA_VERSION,
    SIMILARITY,
    VECTOR_INDEX_OPTIONS,
    ChunkDocument,
    InvalidDocumentState,
    RetrievalIndexUnavailable,
    configured_index_meta,
    create_write_generation,
    resolve_read_target_and_recipe,
    resolve_write_target,
)
from kitsune.retrieval.locks import DocumentLockUnavailable, lifecycle_lock
from kitsune.retrieval.sync import sync_document_chunks
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.search.es_utils import es_client
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory

TS1 = datetime(2026, 1, 1, tzinfo=UTC)
TS2 = datetime(2026, 1, 2, tzinfo=UTC)
OTHER_SCHEMA_VERSION = SCHEMA_VERSION + 1
RETRIEVAL_INIT = "kitsune.retrieval.management.commands.retrieval_init"


def _meta(*, schema_version=SCHEMA_VERSION, **recipe_overrides):
    recipe = configured_embedding_recipe()
    if recipe_overrides:
        recipe = replace(recipe, **recipe_overrides)
    return build_index_meta(
        recipe,
        similarity=SIMILARITY,
        index_options=VECTOR_INDEX_OPTIONS,
        schema_version=schema_version,
    )


def _write_alias():
    return ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)


def _read_alias():
    return ChunkDocument.alias_points_at(ChunkDocument.Index.read_alias)


def _event(logs, name):
    [event] = [record for record in logs.records if record.getMessage() == name]
    return event


def _approved_document():
    document = DocumentFactory(title="Install Firefox", slug="install-firefox")
    ApprovedRevisionFactory(document=document, summary="How to install.")
    document.refresh_from_db()
    return document


class LifecycleTestCase(ChunkIndexTestCase):
    """Each test owns its generations/aliases: start and end on a clean slate, and skip the
    base's document-clearing tearDown (which assumes the write alias exists)."""

    def setUp(self):
        super().setUp()
        self._delete_indices()

    def tearDown(self):
        self._delete_indices()
        # skip ChunkIndexTestCase.tearDown (it delete_by_query's the write alias, which some
        # of these tests intentionally leave unset); go straight to ElasticTestCase.
        super(ChunkIndexTestCase, self).tearDown()


class CreateWriteGenerationTests(LifecycleTestCase):
    def test_stamps_meta_before_moving_the_write_alias(self):
        meta = configured_index_meta()
        name = create_write_generation(timestamp=TS1, meta=meta)
        self.assertEqual(_write_alias(), name)
        self.assertEqual(read_index_meta(name), meta)
        self.assertEqual(classify_meta_mismatch(meta, meta), IndexMetaAction.NONE)
        self.assertEqual(meta["mapping"]["index_options"], VECTOR_INDEX_OPTIONS)
        self.assertEqual(meta["mapping"]["schema_version"], SCHEMA_VERSION)
        # first-run safety: creating a generation must not attach the read alias
        self.assertIsNone(_read_alias())

    def test_does_not_move_write_alias_if_stamping_fails(self):
        with (
            mock.patch(
                "kitsune.retrieval.index.write_index_meta", side_effect=RuntimeError("boom")
            ),
            self.assertRaises(RuntimeError),
        ):
            create_write_generation(timestamp=TS1, meta=configured_index_meta())
        # the un-stamped index must never be reachable through the write alias
        self.assertIsNone(_write_alias())

    def test_rejects_meta_that_does_not_describe_the_created_mapping(self):
        recipe = configured_embedding_recipe()
        incompatible = build_index_meta(
            recipe,
            similarity=SIMILARITY,
            index_options={**VECTOR_INDEX_OPTIONS, "m": VECTOR_INDEX_OPTIONS["m"] + 1},
            schema_version=SCHEMA_VERSION,
        )

        with (
            mock.patch.object(ChunkDocument, "init", wraps=ChunkDocument.init) as init,
            self.assertRaises(InvalidIndexMeta),
        ):
            create_write_generation(timestamp=TS1, meta=incompatible)

        init.assert_not_called()
        self.assertIsNone(_write_alias())


class ResolveWriteTargetTests(LifecycleTestCase):
    def test_tracks_only_the_write_alias(self):
        self.assertIsNone(resolve_write_target())
        first = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        self.assertEqual(resolve_write_target(), first)

        ChunkDocument.migrate_reads()
        self.assertEqual(resolve_write_target(), first)

        second = create_write_generation(timestamp=TS2, meta=configured_index_meta())
        self.assertEqual(resolve_write_target(), second)


class ResolveReadTargetTests(LifecycleTestCase):
    def test_returns_concrete_read_index_and_its_recipe(self):
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        target, recipe = resolve_read_target_and_recipe()
        self.assertEqual(target, name)
        self.assertEqual(recipe, configured_embedding_recipe())

    def test_raises_rather_than_falling_back_to_write_alias(self):
        create_write_generation(timestamp=TS1, meta=configured_index_meta())  # write only
        with self.assertRaises(RetrievalIndexUnavailable):
            resolve_read_target_and_recipe()

    def test_fails_closed_on_invalid_read_meta(self):
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        tampered = configured_index_meta()
        tampered["embedding"]["model"] = "swapped"  # digest no longer matches payload
        es_client().indices.put_mapping(index=name, meta=tampered)
        with self.assertRaises(InvalidIndexMeta):
            resolve_read_target_and_recipe()

    def test_binds_to_the_physical_index_resolved_at_call_time(self):
        first = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        resolved_first, _ = resolve_read_target_and_recipe()

        second = create_write_generation(timestamp=TS2, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        resolved_second, _ = resolve_read_target_and_recipe()

        self.assertEqual(resolved_first, first)
        self.assertEqual(resolved_second, second)


class RetrievalInitCommandTests(LifecycleTestCase):
    def test_first_run_creates_write_generation_without_a_read_alias(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            call_command("retrieval_init")

        write_index = _write_alias()
        self.assertTrue(write_index)
        self.assertIsNone(_read_alias())
        self.assertEqual(read_index_meta(write_index), configured_index_meta())
        event = _event(logs, "retrieval.rebuild.write_initialized")
        self.assertEqual(event.index, write_index)

    def test_compatible_config_updates_mapping_in_place_without_moving_aliases(self):
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        with mock.patch.object(ChunkDocument, "init", wraps=ChunkDocument.init) as init:
            call_command("retrieval_init")
        init.assert_called_once_with(index=name)
        self.assertEqual(_write_alias(), name)
        self.assertEqual(_read_alias(), name)

    def test_fingerprint_mismatch_reports_and_exits_without_moving_aliases(self):
        name = create_write_generation(timestamp=TS1, meta=_meta(model="prior-model"))
        ChunkDocument.migrate_reads()
        with self.assertRaises(CommandError):
            call_command("retrieval_init")
        self.assertEqual(_write_alias(), name)
        self.assertEqual(_read_alias(), name)

    def test_query_recipe_mismatch_names_the_supported_update_command(self):
        create_write_generation(timestamp=TS1, meta=_meta(query_task="PRIOR_QUERY"))
        ChunkDocument.migrate_reads()

        with self.assertRaises(CommandError) as caught:
            call_command("retrieval_init")

        self.assertIn("retrieval_init --update-query-recipe", str(caught.exception))

    def test_query_recipe_update_rewrites_only_the_query_section(self):
        name = create_write_generation(timestamp=TS1, meta=_meta(query_task="PRIOR_QUERY"))
        ChunkDocument.migrate_reads()
        before = read_index_meta(name)
        call_command("retrieval_init", "--update-query-recipe")
        after = read_index_meta(name)
        self.assertEqual(after["embedding"], before["embedding"])
        self.assertEqual(after["mapping"], before["mapping"])
        self.assertEqual(after["query"], configured_index_meta()["query"])

    def test_query_recipe_update_refuses_a_non_query_change(self):
        name = create_write_generation(timestamp=TS1, meta=_meta(model="prior-model"))
        ChunkDocument.migrate_reads()
        with self.assertRaises(CommandError):
            call_command("retrieval_init", "--update-query-recipe")
        self.assertEqual(read_index_meta(name)["embedding"]["model"], "prior-model")

    def test_query_recipe_update_refuses_during_a_rebuild(self):
        read_index = create_write_generation(timestamp=TS1, meta=_meta(query_task="PRIOR_QUERY"))
        ChunkDocument.migrate_reads()
        write_index = create_write_generation(timestamp=TS2, meta=_meta(query_task="PRIOR_QUERY"))

        with self.assertRaises(CommandError):
            call_command("retrieval_init", "--update-query-recipe")

        self.assertEqual(read_index_meta(read_index)["query"]["query_task"], "PRIOR_QUERY")
        self.assertEqual(read_index_meta(write_index)["query"]["query_task"], "PRIOR_QUERY")

    def test_unsupported_option_combinations_fail_without_creating_aliases(self):
        combinations = (
            ("--update-query-recipe", "--start-rebuild"),
            ("--start-rebuild", "--migrate-reads"),
        )
        for options in combinations:
            with self.subTest(options=options), self.assertRaises(CommandError):
                call_command("retrieval_init", *options)
            self.assertIsNone(_write_alias())
            self.assertIsNone(_read_alias())


class AuthorizedRebuildTests(LifecycleTestCase):
    """Creating a generation is the expensive, irreversible step, so it is never implicit."""

    def test_rebuild_is_refused_when_configuration_is_compatible(self):
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()

        with self.assertRaises(CommandError):
            call_command("retrieval_init", "--start-rebuild")

        self.assertEqual(_write_alias(), name)
        self.assertEqual(_read_alias(), name)

    def test_embedding_change_starts_a_full_rebuild(self):
        first = create_write_generation(timestamp=TS1, meta=_meta(model="prior-model"))
        ChunkDocument.migrate_reads()
        out = StringIO()

        with self.assertLogs("k.retrieval", level="INFO") as logs:
            call_command("retrieval_init", "--start-rebuild", stdout=out)

        second = _write_alias()
        self.assertNotEqual(second, first)
        self.assertEqual(read_index_meta(second), configured_index_meta())
        # reads stay on the old generation until the gated swap
        self.assertEqual(_read_alias(), first)
        event = _event(logs, "retrieval.rebuild.write_migrated")
        self.assertEqual(event.source_index, first)
        self.assertEqual(event.target_index, second)
        self.assertIn(f"sync_chunks --backfill --index {second}", out.getvalue())

    def test_mapping_change_also_starts_a_full_rebuild(self):
        first = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        write_index_meta(first, _meta(schema_version=OTHER_SCHEMA_VERSION))
        out = StringIO()

        call_command("retrieval_init", "--start-rebuild", stdout=out)

        second = _write_alias()
        self.assertNotEqual(second, first)
        self.assertEqual(_read_alias(), first)
        self.assertEqual(read_index_meta(second), configured_index_meta())
        self.assertIn(f"sync_chunks --backfill --index {second}", out.getvalue())

    def test_an_existing_divergence_cannot_create_a_third_generation(self):
        first = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        second = create_write_generation(timestamp=TS2, meta=_meta(model="prior-model"))

        with self.assertRaises(CommandError) as caught:
            call_command("retrieval_init", "--start-rebuild")

        self.assertIn(second, str(caught.exception))
        self.assertIn("sync_chunks --backfill", str(caught.exception))
        self.assertEqual(_write_alias(), second)
        self.assertEqual(_read_alias(), first)

    def test_a_write_only_first_run_cannot_create_another_generation(self):
        first = create_write_generation(timestamp=TS1, meta=_meta(model="prior-model"))

        with self.assertRaises(CommandError):
            call_command("retrieval_init", "--start-rebuild")

        self.assertEqual(_write_alias(), first)
        self.assertIsNone(_read_alias())


class LifecycleSerializationTests(LifecycleTestCase):
    def test_a_held_lifecycle_lease_refuses_rather_than_waits(self):
        create_write_generation(timestamp=TS1, meta=_meta(model="prior-model"))
        ChunkDocument.migrate_reads()

        with lifecycle_lock(), self.assertRaises(CommandError):
            call_command("retrieval_init", "--start-rebuild")

    def test_alias_state_is_rechecked_under_the_lease(self):
        # A racing operator wins between this command's first look and its lease.
        first = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()

        real_lock = lifecycle_lock
        winner = f"{ChunkDocument.Index.base_name}_{TS2.strftime('%Y%m%d%H%M%S')}"

        @contextmanager
        def race_then_lock(*args, **kwargs):
            create_write_generation(timestamp=TS2, meta=_meta(model="prior-model"))
            with real_lock(*args, **kwargs) as lease:
                yield lease

        with (
            mock.patch(f"{RETRIEVAL_INIT}.lifecycle_lock", race_then_lock),
            self.assertRaises(CommandError),
        ):
            call_command("retrieval_init", "--start-rebuild")

        # the loser must not have created a third generation
        self.assertEqual(_write_alias(), winner)
        self.assertEqual(_read_alias(), first)

    def test_a_lease_lost_during_the_gate_prevents_the_read_swap(self):
        first = create_write_generation(timestamp=TS1, meta=configured_index_meta())

        @contextmanager
        def lost_lease():
            lease = mock.Mock()
            lease.renew.side_effect = DocumentLockUnavailable("lost")
            yield lease

        with (
            mock.patch(f"{RETRIEVAL_INIT}.lifecycle_lock", lost_lease),
            mock.patch(f"{RETRIEVAL_INIT}.gate_index", return_value=mock.Mock(is_clean=True)),
            self.assertRaises(CommandError),
        ):
            call_command("retrieval_init", "--migrate-reads")

        self.assertEqual(_write_alias(), first)
        self.assertIsNone(_read_alias())


class GatedReadMigrationTests(LifecycleTestCase):
    def setUp(self):
        super().setUp()
        self.first = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        self.document = _approved_document()

    def test_a_dirty_gate_refuses_the_swap(self):
        # The document is eligible but was never indexed, so the new generation is incomplete.
        with self.assertRaises(CommandError):
            call_command("retrieval_init", "--migrate-reads")

        self.assertIsNone(_read_alias())

    def test_an_unparseable_index_is_an_operator_error(self):
        with (
            mock.patch(
                f"{RETRIEVAL_INIT}.gate_index",
                side_effect=InvalidDocumentState("indexed document has an unknown kind"),
            ),
            self.assertRaises(CommandError) as caught,
        ):
            call_command("retrieval_init", "--migrate-reads")

        self.assertIn("index state is invalid", str(caught.exception).lower())
        self.assertIsNone(_read_alias())

    def test_a_clean_gate_attaches_reads_on_first_run(self):
        sync_document_chunks(self.document.id)

        call_command("retrieval_init", "--migrate-reads")

        self.assertEqual(_read_alias(), self.first)

    def test_a_clean_gate_swaps_reads_to_the_new_generation(self):
        sync_document_chunks(self.document.id)
        ChunkDocument.migrate_reads()
        second = create_write_generation(timestamp=TS2, meta=configured_index_meta())
        sync_document_chunks(self.document.id, target_index=second)

        with self.assertLogs("k.retrieval", level="INFO") as logs:
            call_command("retrieval_init", "--migrate-reads")

        self.assertEqual(_read_alias(), second)
        event = _event(logs, "retrieval.rebuild.read_migrated")
        self.assertEqual(event.source_index, self.first)
        self.assertEqual(event.target_index, second)
        self.assertTrue(es_client().indices.exists(index=self.first))

    def test_the_gate_runs_against_the_write_target_not_the_read_target(self):
        # The old read generation being healthy says nothing about the one being promoted.
        sync_document_chunks(self.document.id)
        ChunkDocument.migrate_reads()
        create_write_generation(timestamp=TS2, meta=configured_index_meta())

        with self.assertRaises(CommandError):
            call_command("retrieval_init", "--migrate-reads")

        self.assertEqual(_read_alias(), self.first)

    def test_a_clean_but_obsolete_generation_is_not_promoted(self):
        sync_document_chunks(self.document.id)
        write_index_meta(self.first, _meta(query_task="PRIOR_QUERY"))

        with self.assertRaises(CommandError) as caught:
            call_command("retrieval_init", "--migrate-reads")

        self.assertIn(IndexMetaAction.QUERY_META_UPDATE.value, str(caught.exception))
        self.assertIsNone(_read_alias())


class ChunkerGenerationRolloutTests(LifecycleTestCase):
    def test_a_chunker_change_needs_no_physical_rebuild(self):
        # CHUNKING_GENERATION is not part of the index _meta: changed text re-embeds per
        # document through reconciliation instead of forcing a new generation.
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()

        with mock.patch("kitsune.retrieval.chunking.CHUNKING_GENERATION", CHUNKING_GENERATION + 1):
            call_command("retrieval_init")

        self.assertEqual(_write_alias(), name)
        self.assertEqual(_read_alias(), name)
