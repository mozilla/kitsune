from dataclasses import replace
from datetime import UTC, datetime
from unittest import mock

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from kitsune.retrieval.embeddings import configured_embedding_recipe
from kitsune.retrieval.fingerprints import (
    IndexMetaAction,
    InvalidIndexMeta,
    build_index_meta,
    classify_meta_mismatch,
    read_index_meta,
)
from kitsune.retrieval.index import (
    SCHEMA_VERSION,
    SIMILARITY,
    VECTOR_INDEX_OPTIONS,
    ChunkDocument,
    RetrievalIndexUnavailable,
    configured_index_meta,
    create_write_generation,
    resolve_active_targets,
    resolve_read_target_and_recipe,
)
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.search.es_utils import es_client

TS1 = datetime(2026, 1, 1, tzinfo=UTC)
TS2 = datetime(2026, 1, 2, tzinfo=UTC)


def _meta(**recipe_overrides):
    recipe = configured_embedding_recipe()
    if recipe_overrides:
        recipe = replace(recipe, **recipe_overrides)
    return build_index_meta(
        recipe,
        similarity=SIMILARITY,
        index_options=VECTOR_INDEX_OPTIONS,
        schema_version=SCHEMA_VERSION,
    )


def _write_alias():
    return ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)


def _read_alias():
    return ChunkDocument.alias_points_at(ChunkDocument.Index.read_alias)


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


class ConfiguredIndexMetaTests(SimpleTestCase):
    def test_builds_self_consistent_meta_from_settings(self):
        meta = configured_index_meta()
        self.assertEqual(classify_meta_mismatch(meta, meta), IndexMetaAction.NONE)
        self.assertEqual(meta["embedding"]["dimensions"], settings.RETRIEVAL_EMBEDDING_DIMENSIONS)
        self.assertEqual(meta["mapping"]["index_options"], VECTOR_INDEX_OPTIONS)
        self.assertEqual(meta["mapping"]["schema_version"], SCHEMA_VERSION)


class CreateWriteGenerationTests(LifecycleTestCase):
    def test_stamps_meta_before_moving_the_write_alias(self):
        meta = configured_index_meta()
        name = create_write_generation(timestamp=TS1, meta=meta)
        self.assertEqual(_write_alias(), name)
        self.assertEqual(read_index_meta(name), meta)
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


class ResolveActiveTargetsTests(LifecycleTestCase):
    def test_dedupes_when_read_and_write_share_an_index(self):
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        self.assertEqual(resolve_active_targets(), (name,))

    def test_returns_both_when_read_and_write_diverge(self):
        first = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        second = create_write_generation(timestamp=TS2, meta=configured_index_meta())
        self.assertEqual(set(resolve_active_targets()), {first, second})
        self.assertEqual(len(resolve_active_targets()), 2)

    def test_omits_missing_aliases(self):
        self.assertEqual(resolve_active_targets(), ())
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        self.assertEqual(resolve_active_targets(), (name,))


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


class SearchInitCommandTests(LifecycleTestCase):
    def test_first_run_creates_write_generation_without_a_read_alias(self):
        call_command("search_init")
        write_index = _write_alias()
        self.assertTrue(write_index)
        self.assertIsNone(_read_alias())
        self.assertEqual(read_index_meta(write_index), configured_index_meta())

    def test_compatible_config_updates_mapping_in_place_without_moving_aliases(self):
        name = create_write_generation(timestamp=TS1, meta=configured_index_meta())
        ChunkDocument.migrate_reads()
        with mock.patch.object(ChunkDocument, "init", wraps=ChunkDocument.init) as init:
            call_command("search_init")
        init.assert_called_once_with(index=name)
        self.assertEqual(_write_alias(), name)
        self.assertEqual(_read_alias(), name)

    def test_fingerprint_mismatch_reports_and_exits_without_moving_aliases(self):
        name = create_write_generation(timestamp=TS1, meta=_meta(model="prior-model"))
        ChunkDocument.migrate_reads()
        with self.assertRaises(CommandError):
            call_command("search_init")
        self.assertEqual(_write_alias(), name)
        self.assertEqual(_read_alias(), name)

    def test_query_recipe_update_rewrites_only_the_query_section(self):
        name = create_write_generation(timestamp=TS1, meta=_meta(query_task="PRIOR_QUERY"))
        ChunkDocument.migrate_reads()
        before = read_index_meta(name)
        call_command("search_init", "--update-query-recipe")
        after = read_index_meta(name)
        self.assertEqual(after["embedding"], before["embedding"])
        self.assertEqual(after["mapping"], before["mapping"])
        self.assertEqual(after["query"], configured_index_meta()["query"])

    def test_query_recipe_update_refuses_a_non_query_change(self):
        name = create_write_generation(timestamp=TS1, meta=_meta(model="prior-model"))
        ChunkDocument.migrate_reads()
        with self.assertRaises(CommandError):
            call_command("search_init", "--update-query-recipe")
        self.assertEqual(read_index_meta(name)["embedding"]["model"], "prior-model")

    def test_query_recipe_update_preflights_all_targets_before_writing(self):
        read_index = create_write_generation(timestamp=TS1, meta=_meta(query_task="PRIOR_QUERY"))
        ChunkDocument.migrate_reads()
        write_index = create_write_generation(timestamp=TS2, meta=_meta(model="prior-model"))

        with self.assertRaises(CommandError):
            call_command("search_init", "--update-query-recipe")

        self.assertEqual(read_index_meta(read_index)["query"]["query_task"], "PRIOR_QUERY")
        self.assertEqual(read_index_meta(write_index)["embedding"]["model"], "prior-model")

    def test_query_recipe_update_applies_to_all_compatible_active_targets(self):
        read_index = create_write_generation(timestamp=TS1, meta=_meta(query_task="PRIOR_QUERY"))
        ChunkDocument.migrate_reads()
        write_index = create_write_generation(timestamp=TS2, meta=_meta(query_task="PRIOR_QUERY"))

        call_command("search_init", "--update-query-recipe")

        desired_query = configured_index_meta()["query"]
        self.assertEqual(read_index_meta(read_index)["query"], desired_query)
        self.assertEqual(read_index_meta(write_index)["query"], desired_query)

    def test_query_update_cannot_be_combined_with_migration(self):
        with self.assertRaises(CommandError):
            call_command("search_init", "--update-query-recipe", "--migrate-writes")
        self.assertIsNone(_write_alias())
        self.assertIsNone(_read_alias())

    def test_read_migration_is_disabled_until_the_integrity_gate_exists(self):
        write_index = create_write_generation(timestamp=TS1, meta=configured_index_meta())

        with self.assertRaises(CommandError):
            call_command("search_init", "--migrate-reads")

        self.assertEqual(_write_alias(), write_index)
        self.assertIsNone(_read_alias())

    def test_combined_migration_cannot_expose_an_empty_first_generation(self):
        with self.assertRaises(CommandError):
            call_command("search_init", "--migrate-writes", "--migrate-reads")

        self.assertIsNone(_write_alias())
        self.assertIsNone(_read_alias())
