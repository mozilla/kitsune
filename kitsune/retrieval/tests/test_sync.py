from datetime import UTC, datetime
from unittest import mock

from django.test import SimpleTestCase

from kitsune.products.tests import ProductFactory
from kitsune.retrieval.chunking import CHUNKING_GENERATION, Chunk, chunk
from kitsune.retrieval.embeddings import (
    EmbeddingRecipe,
    configured_embedding_recipe,
    get_embeddings,
    recipe_to_payload,
)
from kitsune.retrieval.fingerprints import InvalidIndexMeta, build_index_meta
from kitsune.retrieval.index import (
    CHUNK_KIND,
    SCHEMA_VERSION,
    SIMILARITY,
    VECTOR_INDEX_OPTIONS,
    ChunkDocument,
    ChunkIdentity,
    IncompleteDocumentState,
    IndexWriteError,
    StoredChunkSummary,
    commit_manifest,
    configured_index_meta,
    create_write_generation,
    manifest_id,
    read_indexed_document,
    scope_envelope,
)
from kitsune.retrieval.locks import DocumentLockUnavailable, RedisLease, document_lock
from kitsune.retrieval.sync import (
    SyncOutcome,
    build_source,
    delete_document_chunks,
    plan_target,
    sync_document_chunks,
)
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.retrieval.tests.test_index import _expected, _source, _vector
from kitsune.search.es_utils import es_client
from kitsune.users.tests import GroupFactory
from kitsune.wiki.models import Document
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _chunks(count, *, text="body {i}"):
    return [Chunk(text=text.format(i=i), position=i, heading_path="H") for i in range(count)]


def _stored(chunks, source, state, *, count=None, **overrides):
    """The chunk `_source` dicts a healthy write would have left in one index."""
    documents = []
    for item in chunks[: count if count is not None else len(chunks)]:
        documents.append(
            {
                "kind": CHUNK_KIND,
                "position": item.position,
                "content_text": {source.locale: item.text},
                "content_vector": _vector(item.position),
                "scope": scope_envelope(item.scope),
                "content_hash": state.content_hash,
                "index_state_hash": state.index_state_hash,
                "chunking_generation": state.chunking_generation,
                "visibility": source.visibility,
                "access_group_ids": list(source.access_group_ids),
                **overrides,
            }
        )
    return documents


def _summaries(chunks, source, *, count=None, extra_positions=(), **overrides):
    summaries = [
        StoredChunkSummary(
            item.position,
            overrides.get("visibility", source.visibility),
            overrides.get("access_group_ids", source.access_group_ids),
        )
        for item in chunks[: count if count is not None else len(chunks)]
    ]
    summaries.extend(
        StoredChunkSummary(position, source.visibility, source.access_group_ids)
        for position in extra_positions
    )
    return tuple(summaries)


def _plan(chunks, source, state, *, manifest=..., summaries=None):
    return plan_target(
        chunks=chunks,
        source=source,
        expected_state=state,
        manifest=state if manifest is ... else manifest,
        summaries=_summaries(chunks, source) if summaries is None else summaries,
    )


class PlanOutcomeTests(SimpleTestCase):
    """The planner is pure: expected state plus indexed state decides the outcome, with no
    Elasticsearch, Redis, or database access."""

    def setUp(self):
        self.source = _source()
        self.chunks = _chunks(3)
        self.state = _expected(self.chunks, self.source)

    def test_a_fully_committed_document_is_a_no_op(self):
        self.assertEqual(_plan(self.chunks, self.source, self.state), SyncOutcome.NO_OP)

    def test_an_empty_index_embeds_and_replaces(self):
        plan = _plan(self.chunks, self.source, self.state, manifest=None, summaries=())
        self.assertEqual(plan, SyncOutcome.EMBED_REPLACE)

    def test_changed_text_embeds_and_replaces(self):
        stale = _expected(_chunks(3, text="old {i}"), self.source)
        plan = _plan(self.chunks, self.source, self.state, manifest=stale, summaries=())
        self.assertEqual(plan, SyncOutcome.EMBED_REPLACE)

    def test_a_missing_position_embeds_and_replaces(self):
        plan = _plan(
            self.chunks,
            self.source,
            self.state,
            summaries=_summaries(self.chunks, self.source, count=2),
        )
        self.assertEqual(plan, SyncOutcome.EMBED_REPLACE)

    def test_changed_metadata_alone_takes_the_metadata_path(self):
        # Same committed content, different state hash: no reason to pay the provider again.
        rescoped = _source(product_ids=["9"])
        state = _expected(self.chunks, rescoped)
        plan = _plan(
            self.chunks,
            rescoped,
            state,
            manifest=self.state,
            summaries=_summaries(self.chunks, self.source),
        )
        self.assertEqual(plan, SyncOutcome.METADATA_ONLY)

    def test_a_stale_manifest_takes_the_metadata_path_when_content_matches(self):
        older = _expected(self.chunks, self.source, indexed_revision_id=1)
        state = _expected(self.chunks, self.source, indexed_revision_id=2)
        plan = _plan(self.chunks, self.source, state, manifest=older)
        self.assertEqual(plan, SyncOutcome.METADATA_ONLY)

    def test_leftover_positions_embed_and_replace(self):
        plan = _plan(
            self.chunks,
            self.source,
            self.state,
            summaries=_summaries(self.chunks, self.source, extra_positions=(3, 4)),
        )
        self.assertEqual(plan, SyncOutcome.EMBED_REPLACE)

    def test_a_zero_chunk_document_with_leftovers_replaces_without_provider_input(self):
        empty = _chunks(0)
        state = _expected(empty, self.source)
        plan = _plan(
            empty,
            self.source,
            state,
            manifest=None,
            summaries=_summaries(self.chunks, self.source),
        )
        self.assertEqual(plan, SyncOutcome.EMBED_REPLACE)

    def test_a_committed_zero_chunk_document_is_a_no_op(self):
        empty = _chunks(0)
        state = _expected(empty, self.source)
        self.assertEqual(_plan(empty, self.source, state, summaries=()), SyncOutcome.NO_OP)

    def test_access_drift_hidden_behind_a_current_manifest_is_metadata_only(self):
        summaries = _summaries(
            self.chunks,
            self.source,
            visibility="group_restricted",
            access_group_ids=(7,),
        )
        self.assertEqual(
            _plan(self.chunks, self.source, self.state, summaries=summaries),
            SyncOutcome.METADATA_ONLY,
        )


class StalenessDefenceTests(SimpleTestCase):
    """A worker holding older content must never overwrite a newer commit, lease or not."""

    def setUp(self):
        self.source = _source()
        self.chunks = _chunks(2)

    def test_a_newer_stored_revision_aborts(self):
        state = _expected(self.chunks, self.source, indexed_revision_id=2)
        newer = _expected(self.chunks, self.source, indexed_revision_id=5)
        plan = _plan(self.chunks, self.source, state, manifest=newer)
        self.assertEqual(plan, SyncOutcome.ABORTED_STALE)

    def test_a_newer_stored_chunking_generation_aborts(self):
        state = _expected(self.chunks, self.source)
        newer = _expected(self.chunks, self.source, chunking_generation=CHUNKING_GENERATION + 1)
        plan = _plan(self.chunks, self.source, state, manifest=newer)
        self.assertEqual(plan, SyncOutcome.ABORTED_STALE)

    def test_an_equal_revision_is_not_stale(self):
        state = _expected(self.chunks, self.source, indexed_revision_id=3)
        self.assertEqual(_plan(self.chunks, self.source, state), SyncOutcome.NO_OP)

    def test_staleness_is_decided_before_anything_would_be_embedded(self):
        # A newer manifest must abort before its mismatched content could select replacement.
        state = _expected(self.chunks, self.source, indexed_revision_id=1)
        newer = _expected(self.chunks, self.source, indexed_revision_id=9)
        plan = _plan(self.chunks, self.source, state, manifest=newer, summaries=())
        self.assertEqual(plan, SyncOutcome.ABORTED_STALE)


class SyncExecutorTests(ChunkIndexTestCase):
    """The executor against real Elasticsearch, a real lease, and the deterministic fake."""

    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        self.document = DocumentFactory(title="Install Firefox", slug="install-firefox")
        ApprovedRevisionFactory(
            document=self.document, summary="How to install.", keywords="setup"
        )
        self.document.refresh_from_db()
        self.identity = ChunkIdentity("kb", str(self.document.id), self.document.locale)

    def _sync(self, **kwargs):
        return sync_document_chunks(self.document.id, **kwargs)

    def _stored_state(self):
        return read_indexed_document(index=self.index, identity=self.identity)

    def test_a_first_sync_embeds_and_commits(self):
        report = self._sync()

        self.assertEqual((report.index, report.outcome), (self.index, SyncOutcome.EMBED_REPLACE))
        self.assertEqual(report.embedding_calls, 1)
        stored = self._stored_state()
        self.assertGreater(len(stored.chunks), 0)
        self.assertEqual(stored.manifest.chunk_count, len(stored.chunks))
        self.assertEqual(stored.manifest.indexed_revision_id, self.document.current_revision_id)

    def test_the_provider_receives_the_exact_chunker_text(self):
        expected_texts = [
            item.text for item in chunk("kb", self.document.html, title=self.document.title)
        ]
        with mock.patch(
            "kitsune.retrieval.sync.get_embeddings", side_effect=get_embeddings
        ) as embed:
            self._sync()
        self.assertEqual(embed.call_args.args[0], expected_texts)

    def test_an_unchanged_document_is_a_no_op_without_embedding(self):
        self._sync()
        report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.NO_OP)
        self.assertEqual(report.embedding_calls, 0)

    def test_a_metadata_change_updates_without_embedding(self):
        self._sync()
        vector_before = self._stored_state().chunks[0]["content_vector"]

        self.document.products.add(ProductFactory())
        report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.METADATA_ONLY)
        self.assertEqual(report.embedding_calls, 0)
        stored = self._stored_state()
        vector_after = stored.chunks[0]["content_vector"]
        self.assertEqual(len(vector_after), len(vector_before))
        for before, after in zip(vector_before, vector_after, strict=True):
            self.assertAlmostEqual(before, after, places=6)
        self.assertNotEqual(stored.chunks[0]["product_ids"], [])

    def test_changed_content_re_embeds(self):
        self._sync()
        ApprovedRevisionFactory(document=self.document, content="Totally different guidance.")
        self.document.refresh_from_db()

        report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.EMBED_REPLACE)
        self.assertEqual(report.embedding_calls, 1)

    def test_a_missing_manifest_is_replaced(self):
        self._sync()
        es_client().delete(index=self.index, id=manifest_id(self.identity), refresh=True)

        report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.EMBED_REPLACE)
        self.assertEqual(report.embedding_calls, 1)
        self.assertIsNotNone(self._stored_state().manifest)

    def test_a_missing_metadata_target_falls_back_to_replacement(self):
        self._sync()
        self.document.products.add(ProductFactory())

        with (
            mock.patch(
                "kitsune.retrieval.sync.update_chunks_metadata_for",
                side_effect=IncompleteDocumentState("position disappeared"),
            ),
            mock.patch("kitsune.retrieval.sync.get_embeddings", wraps=get_embeddings) as embed,
        ):
            report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.EMBED_REPLACE)
        self.assertEqual(report.embedding_calls, 1)
        embed.assert_called_once()
        self.assertEqual(self._sync().outcome, SyncOutcome.NO_OP)

    def test_an_ineligible_document_is_evicted(self):
        self._sync()
        self.document.restrict_to_groups.add(GroupFactory())

        with self.assertLogs("k.retrieval", level="INFO") as logs:
            report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.DELETED)
        self.assertEqual(logs.records[0].outcome, "deleted")
        stored = self._stored_state()
        self.assertEqual(stored.chunks, [])
        self.assertIsNone(stored.manifest)

    def test_a_deleted_row_is_evicted_by_object(self):
        self._sync()
        document_id = self.document.id
        self.document.delete()

        report = sync_document_chunks(document_id)

        self.assertEqual(report.outcome, SyncOutcome.DELETED)
        self.assertEqual(self._stored_state().chunks, [])

    def test_delete_document_chunks_removes_everything(self):
        self._sync()

        report = delete_document_chunks(self.identity)

        self.assertEqual(report.outcome, SyncOutcome.DELETED)
        stored = self._stored_state()
        self.assertEqual(stored.chunks, [])
        self.assertIsNone(stored.manifest)

    def test_an_explicit_target_does_not_fan_out(self):
        report = self._sync(target_index=self.index)
        self.assertEqual(report.index, self.index)

    def test_no_write_target_writes_nothing(self):
        with (
            mock.patch("kitsune.retrieval.sync.resolve_write_target", return_value=None),
            self.assertLogs("k.retrieval", level="WARNING") as logs,
        ):
            report = self._sync()
        self.assertIsNone(report.outcome)
        self.assertEqual(report.embedding_calls, 0)
        self.assertEqual(logs.records[0].getMessage(), "retrieval.sync.skipped")

    def test_unreadable_target_meta_fails_before_the_provider(self):
        with (
            mock.patch(
                "kitsune.retrieval.sync.recipe_for_index",
                side_effect=InvalidIndexMeta("tampered"),
            ),
            mock.patch("kitsune.retrieval.sync.get_embeddings") as embed,
            self.assertRaises(InvalidIndexMeta),
        ):
            self._sync()
        embed.assert_not_called()

    def test_a_revision_change_during_provider_work_aborts_without_writing(self):
        def edit_then_embed(*args, **kwargs):
            ApprovedRevisionFactory(document=self.document, content="Raced edit.")
            return get_embeddings(*args, **kwargs)

        with mock.patch("kitsune.retrieval.sync.get_embeddings", side_effect=edit_then_embed):
            report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.ABORTED_STALE)
        stored = self._stored_state()
        self.assertEqual(stored.chunks, [])
        self.assertIsNone(stored.manifest)

    def test_a_same_revision_html_change_during_provider_work_aborts(self):
        revision_id = self.document.current_revision_id

        def rerender_then_embed(*args, **kwargs):
            Document.objects.filter(pk=self.document.id).update(html="<p>Rerendered include.</p>")
            return get_embeddings(*args, **kwargs)

        with mock.patch("kitsune.retrieval.sync.get_embeddings", side_effect=rerender_then_embed):
            report = self._sync()

        self.document.refresh_from_db()
        self.assertEqual(self.document.current_revision_id, revision_id)
        self.assertEqual(report.outcome, SyncOutcome.ABORTED_STALE)
        self.assertEqual(self._stored_state().chunks, [])

    def test_a_restriction_during_provider_work_evicts_instead_of_writing(self):
        self._sync()

        def restrict_then_embed(*args, **kwargs):
            self.document.restrict_to_groups.add(GroupFactory())
            return get_embeddings(*args, **kwargs)

        ApprovedRevisionFactory(document=self.document, content="New content to force embed.")
        self.document.refresh_from_db()
        with mock.patch("kitsune.retrieval.sync.get_embeddings", side_effect=restrict_then_embed):
            report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.DELETED)
        self.assertEqual(self._stored_state().chunks, [])

    def test_a_lost_lease_cannot_evict_after_provider_work(self):
        self._sync()
        committed = self._stored_state().manifest
        ApprovedRevisionFactory(document=self.document, content="New content to force embed.")
        self.document.refresh_from_db()

        def restrict_then_embed(*args, **kwargs):
            self.document.restrict_to_groups.add(GroupFactory())
            return get_embeddings(*args, **kwargs)

        with (
            mock.patch("kitsune.retrieval.sync.get_embeddings", side_effect=restrict_then_embed),
            mock.patch.object(RedisLease, "renew", side_effect=DocumentLockUnavailable("stolen")),
            self.assertRaises(DocumentLockUnavailable),
        ):
            self._sync()

        self.assertEqual(self._stored_state().manifest, committed)

    def test_a_lost_lease_writes_nothing(self):
        with (
            mock.patch.object(RedisLease, "renew", side_effect=DocumentLockUnavailable("stolen")),
            self.assertRaises(DocumentLockUnavailable),
        ):
            self._sync()

        self.assertEqual(self._stored_state().chunks, [])

    def test_a_contended_document_is_not_synced_twice(self):
        with document_lock(self.identity), self.assertRaises(DocumentLockUnavailable):
            self._sync()
        self.assertEqual(self._stored_state().chunks, [])

    def test_a_stale_worker_cannot_overwrite_a_newer_commit(self):
        self._sync()
        newer = self._stored_state().manifest
        # Stand in for a concurrent worker that already committed a later revision.
        commit_manifest(
            index=self.index,
            identity=self.identity,
            expected_state=_expected(
                chunk("kb", self.document.html, title=self.document.title),
                build_source(self.document),
                indexed_revision_id=newer.indexed_revision_id + 5,
            ),
        )

        report = self._sync()

        self.assertEqual(report.outcome, SyncOutcome.ABORTED_STALE)
        self.assertEqual(report.embedding_calls, 0)

    def test_the_completion_event_carries_no_text_or_vectors(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            self._sync()
        [record] = [r for r in logs.records if r.getMessage() == "retrieval.sync.completed"]
        self.assertEqual(
            (record.index, record.outcome), (self.index, SyncOutcome.EMBED_REPLACE.value)
        )
        self.assertNotIn("Install Firefox", repr(record.__dict__))
        for field in ("content_text", "content_vector", "access_group_ids"):
            self.assertNotIn(field, record.__dict__)


class BuildSourceTests(ChunkIndexTestCase):
    def test_a_translation_inherits_its_originals_metadata(self):
        parent = DocumentFactory(title="Parent", slug="parent")
        ApprovedRevisionFactory(document=parent)
        product = ProductFactory()
        parent.products.add(product)
        translation = DocumentFactory(parent=parent, locale="de", title="Eltern", slug="eltern")
        ApprovedRevisionFactory(document=translation, summary="Wie man installiert.")
        translation.refresh_from_db()

        source = build_source(translation)

        self.assertEqual(source.locale, "de")
        self.assertEqual(source.title, "Eltern")  # its own localized text
        self.assertEqual(source.family_id, str(parent.id))  # the family key
        self.assertEqual(source.product_ids, (str(product.id),))  # inherited
        self.assertEqual(source.visibility, "public")
        self.assertEqual(source.access_group_ids, ())


class SingleWriteGenerationTests(ChunkIndexTestCase):
    """During a rebuild, ordinary mutations touch only the write generation."""

    def setUp(self):
        super().setUp()
        self.first = ChunkDocument.alias_points_at(ChunkDocument.Index.read_alias)
        self.document = DocumentFactory(title="Install Firefox", slug="install-firefox")
        ApprovedRevisionFactory(document=self.document, summary="How to install.")
        self.document.refresh_from_db()
        self.identity = ChunkIdentity("kb", str(self.document.id), self.document.locale)

    def _second_generation(self, recipe=None):
        """Add a generation the write alias points at, leaving reads on the first."""
        meta = (
            configured_index_meta()
            if recipe is None
            else build_index_meta(
                recipe,
                similarity=SIMILARITY,
                index_options=VECTOR_INDEX_OPTIONS,
                schema_version=SCHEMA_VERSION,
            )
        )
        return create_write_generation(timestamp=datetime(2031, 5, 4, tzinfo=UTC), meta=meta)

    def test_an_ordinary_sync_writes_only_to_the_new_generation(self):
        second = self._second_generation()

        report = sync_document_chunks(self.document.id)

        self.assertEqual((report.index, report.outcome), (second, SyncOutcome.EMBED_REPLACE))
        self.assertEqual(report.embedding_calls, 1)
        self.assertEqual(
            read_indexed_document(index=self.first, identity=self.identity).chunks, []
        )
        self.assertGreater(
            len(read_indexed_document(index=second, identity=self.identity).chunks), 0
        )

    def test_sync_uses_only_the_write_generations_recipe(self):
        other_space = EmbeddingRecipe(
            **{**recipe_to_payload(configured_embedding_recipe()), "model": "another-model"}
        )
        second = self._second_generation(other_space)

        with mock.patch("kitsune.retrieval.sync.get_embeddings", wraps=get_embeddings) as embed:
            report = sync_document_chunks(self.document.id)

        self.assertEqual(report.index, second)
        self.assertEqual(report.embedding_calls, 1)
        self.assertEqual(embed.call_args.kwargs["recipe"], other_space)

    def test_ineligibility_evicts_only_from_the_write_generation(self):
        # Seed the complete old read generation explicitly; earlier tests may already have
        # left this test class's write alias diverged from it.
        sync_document_chunks(self.document.id, target_index=self.first)
        second = self._second_generation()
        sync_document_chunks(self.document.id)
        self.document.restrict_to_groups.add(GroupFactory())

        report = sync_document_chunks(self.document.id)

        self.assertEqual((report.index, report.outcome), (second, SyncOutcome.DELETED))
        self.assertGreater(
            len(read_indexed_document(index=self.first, identity=self.identity).chunks), 0
        )
        stored = read_indexed_document(index=second, identity=self.identity)
        self.assertEqual(stored.chunks, [])
        self.assertIsNone(stored.manifest)

    def test_newer_state_in_the_read_generation_does_not_block_the_write_generation(self):
        expected = _expected(
            chunk("kb", self.document.html, title=self.document.title),
            build_source(self.document),
            indexed_revision_id=self.document.current_revision_id + 1,
        )
        commit_manifest(index=self.first, identity=self.identity, expected_state=expected)
        second = self._second_generation()

        report = sync_document_chunks(self.document.id)

        self.assertEqual((report.index, report.outcome), (second, SyncOutcome.EMBED_REPLACE))
        self.assertEqual(report.embedding_calls, 1)
        self.assertGreater(
            len(read_indexed_document(index=second, identity=self.identity).chunks), 0
        )


class FailureContainmentTests(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        self.document = DocumentFactory(title="Install Firefox", slug="install-firefox")
        ApprovedRevisionFactory(document=self.document, summary="How to install.")
        self.document.refresh_from_db()
        self.identity = ChunkIdentity("kb", str(self.document.id), self.document.locale)

    def _stored(self):
        return read_indexed_document(index=self.index, identity=self.identity)

    def test_a_provider_failure_never_advances_the_manifest(self):
        with (
            mock.patch(
                "kitsune.retrieval.sync.get_embeddings", side_effect=RuntimeError("provider down")
            ),
            self.assertRaises(RuntimeError),
        ):
            sync_document_chunks(self.document.id)

        stored = self._stored()
        self.assertEqual(stored.chunks, [])
        self.assertIsNone(stored.manifest)

    def test_an_elasticsearch_failure_never_advances_the_manifest(self):
        sync_document_chunks(self.document.id)
        committed = self._stored().manifest
        ApprovedRevisionFactory(document=self.document, content="Replacement content.")
        self.document.refresh_from_db()

        with (
            mock.patch(
                "kitsune.retrieval.sync.replace_chunks", side_effect=IndexWriteError("bulk failed")
            ),
            self.assertRaises(IndexWriteError),
        ):
            sync_document_chunks(self.document.id)

        # The previous commit stands; a half-written replacement must not look complete.
        self.assertEqual(self._stored().manifest, committed)

    def test_a_general_metadata_failure_does_not_trigger_paid_fallback(self):
        sync_document_chunks(self.document.id)
        committed = self._stored().manifest
        self.document.products.add(ProductFactory())

        with (
            mock.patch(
                "kitsune.retrieval.sync.update_chunks_metadata_for",
                side_effect=IndexWriteError("bulk failed"),
            ),
            mock.patch("kitsune.retrieval.sync.get_embeddings") as embed,
            self.assertRaises(IndexWriteError),
        ):
            sync_document_chunks(self.document.id)

        embed.assert_not_called()
        self.assertEqual(self._stored().manifest, committed)

    def test_a_document_with_no_chunkable_content_commits_an_empty_manifest(self):
        Document.objects.filter(pk=self.document.id).update(html="")

        report = sync_document_chunks(self.document.id)

        stored = self._stored()
        self.assertEqual(stored.chunks, [])
        # "Processed and empty" has to be distinguishable from "never processed".
        self.assertIsNotNone(stored.manifest)
        self.assertEqual(stored.manifest.chunk_count, 0)
        # Replacement still owns the cleanup and manifest; an empty input costs no API call.
        self.assertEqual(report.outcome, SyncOutcome.EMBED_REPLACE)
        self.assertEqual(report.embedding_calls, 0)
