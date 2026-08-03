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
    VECTOR_DIMS,
    VECTOR_INDEX_OPTIONS,
    ChunkDocument,
    ChunkIdentity,
    IndexedDocumentState,
    IndexWriteError,
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


def _indexed(chunks, source, state, *, manifest=..., extra_positions=(), **overrides):
    documents = _stored(chunks, source, state, **overrides)
    for position in extra_positions:
        leftover = dict(documents[0], position=position)
        documents.append(leftover)
    return IndexedDocumentState(
        manifest=state if manifest is ... else manifest,
        chunks=sorted(documents, key=lambda c: c["position"]),
    )


def _plan(chunks, source, state, indexed, recipe=None):
    return plan_target(
        chunks=chunks,
        source=source,
        expected_state=state,
        indexed=indexed,
        recipe=recipe or configured_embedding_recipe(),
    )


class PlanOutcomeTests(SimpleTestCase):
    """The planner is pure: expected state plus indexed state decides the outcome, with no
    Elasticsearch, Redis, or database access."""

    def setUp(self):
        self.source = _source()
        self.chunks = _chunks(3)
        self.state = _expected(self.chunks, self.source)

    def test_a_fully_committed_document_is_a_no_op(self):
        indexed = _indexed(self.chunks, self.source, self.state)
        self.assertEqual(
            _plan(self.chunks, self.source, self.state, indexed).outcome, SyncOutcome.NO_OP
        )

    def test_an_empty_index_embeds_and_replaces(self):
        indexed = IndexedDocumentState(manifest=None, chunks=[])
        plan = _plan(self.chunks, self.source, self.state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.EMBED_REPLACE)

    def test_changed_text_embeds_and_replaces(self):
        stale = _expected(_chunks(3, text="old {i}"), self.source)
        indexed = _indexed(_chunks(3, text="old {i}"), self.source, stale)
        plan = _plan(self.chunks, self.source, self.state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.EMBED_REPLACE)

    def test_a_missing_position_embeds_and_replaces(self):
        indexed = _indexed(self.chunks, self.source, self.state, count=2)
        plan = _plan(self.chunks, self.source, self.state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.EMBED_REPLACE)

    def test_a_malformed_vector_embeds_and_replaces(self):
        for vector in (
            [],
            [0.0] * (VECTOR_DIMS - 1),
            [float("nan")] * VECTOR_DIMS,
            [True] * VECTOR_DIMS,
            None,
        ):
            with self.subTest(vector=vector):
                indexed = _indexed(self.chunks, self.source, self.state, content_vector=vector)
                plan = _plan(self.chunks, self.source, self.state, indexed)
                self.assertEqual(plan.outcome, SyncOutcome.EMBED_REPLACE)

    def test_malformed_stored_text_embeds_and_replaces(self):
        for stored_text in (None, "body", []):
            with self.subTest(stored_text=stored_text):
                indexed = _indexed(
                    self.chunks,
                    self.source,
                    self.state,
                    content_text=stored_text,
                )
                self.assertEqual(
                    _plan(self.chunks, self.source, self.state, indexed).outcome,
                    SyncOutcome.EMBED_REPLACE,
                )

    def test_a_vector_that_breaks_the_recipe_normalization_is_replaced(self):
        recipe = EmbeddingRecipe(
            **{**recipe_to_payload(configured_embedding_recipe()), "normalization": "l2"}
        )
        indexed = _indexed(
            self.chunks,
            self.source,
            self.state,
            content_vector=[2.0] + [0.0] * (VECTOR_DIMS - 1),
        )
        self.assertEqual(
            _plan(self.chunks, self.source, self.state, indexed, recipe).outcome,
            SyncOutcome.EMBED_REPLACE,
        )

    def test_changed_metadata_alone_takes_the_metadata_path(self):
        # Same text and vectors, different state hash: no reason to pay the provider again.
        rescoped = _source(product_ids=["9"])
        state = _expected(self.chunks, rescoped)
        indexed = _indexed(self.chunks, self.source, self.state)
        plan = _plan(self.chunks, rescoped, state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.METADATA_ONLY)

    def test_a_missing_manifest_is_only_a_commit_repair(self):
        indexed = _indexed(self.chunks, self.source, self.state, manifest=None)
        plan = _plan(self.chunks, self.source, self.state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.COMMIT_REPAIR)
        self.assertEqual(plan.orphan_positions, ())

    def test_a_stale_manifest_is_only_a_commit_repair(self):
        older = _expected(self.chunks, self.source, indexed_revision_id=1)
        state = _expected(self.chunks, self.source, indexed_revision_id=2)
        indexed = _indexed(self.chunks, self.source, state, manifest=older)
        plan = _plan(self.chunks, self.source, state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.COMMIT_REPAIR)

    def test_leftover_positions_are_reported_for_repair(self):
        indexed = _indexed(self.chunks, self.source, self.state, extra_positions=(3, 4))
        plan = _plan(self.chunks, self.source, self.state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.COMMIT_REPAIR)
        self.assertEqual(plan.orphan_positions, (3, 4))

    def test_a_zero_chunk_document_with_leftovers_repairs(self):
        empty = _chunks(0)
        state = _expected(empty, self.source)
        indexed = IndexedDocumentState(
            manifest=None, chunks=_stored(self.chunks, self.source, self.state)
        )
        plan = _plan(empty, self.source, state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.COMMIT_REPAIR)
        self.assertEqual(plan.orphan_positions, (0, 1, 2))

    def test_a_committed_zero_chunk_document_is_a_no_op(self):
        empty = _chunks(0)
        state = _expected(empty, self.source)
        indexed = IndexedDocumentState(manifest=state, chunks=[])
        self.assertEqual(_plan(empty, self.source, state, indexed).outcome, SyncOutcome.NO_OP)


class StalenessDefenceTests(SimpleTestCase):
    """A worker holding older content must never overwrite a newer commit, lease or not."""

    def setUp(self):
        self.source = _source()
        self.chunks = _chunks(2)

    def test_a_newer_stored_revision_aborts(self):
        state = _expected(self.chunks, self.source, indexed_revision_id=2)
        newer = _expected(self.chunks, self.source, indexed_revision_id=5)
        indexed = _indexed(self.chunks, self.source, newer)
        plan = _plan(self.chunks, self.source, state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.ABORTED_STALE)

    def test_a_newer_stored_chunking_generation_aborts(self):
        state = _expected(self.chunks, self.source)
        newer = _expected(self.chunks, self.source, chunking_generation=CHUNKING_GENERATION + 1)
        indexed = _indexed(self.chunks, self.source, newer)
        plan = _plan(self.chunks, self.source, state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.ABORTED_STALE)

    def test_a_newer_generation_on_the_chunks_alone_aborts(self):
        # A crash can leave newer chunks with no manifest; downgrading them is still wrong.
        state = _expected(self.chunks, self.source)
        indexed = _indexed(
            self.chunks,
            self.source,
            state,
            manifest=None,
            chunking_generation=CHUNKING_GENERATION + 1,
        )
        plan = _plan(self.chunks, self.source, state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.ABORTED_STALE)

    def test_an_equal_revision_is_not_stale(self):
        state = _expected(self.chunks, self.source, indexed_revision_id=3)
        indexed = _indexed(self.chunks, self.source, state)
        self.assertEqual(
            _plan(self.chunks, self.source, state, indexed).outcome, SyncOutcome.NO_OP
        )

    def test_staleness_is_decided_before_anything_would_be_embedded(self):
        # Newer stored state plus unusable chunk bodies: it must abort rather than re-embed.
        state = _expected(self.chunks, self.source, indexed_revision_id=1)
        newer = _expected(self.chunks, self.source, indexed_revision_id=9)
        indexed = _indexed(self.chunks, self.source, newer, content_vector=None)
        plan = _plan(self.chunks, self.source, state, indexed)
        self.assertEqual(plan.outcome, SyncOutcome.ABORTED_STALE)


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

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.EMBED_REPLACE})
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

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.NO_OP})
        self.assertEqual(report.embedding_calls, 0)

    def test_a_metadata_change_updates_without_embedding(self):
        self._sync()
        vector_before = self._stored_state().chunks[0]["content_vector"]

        self.document.products.add(ProductFactory())
        report = self._sync()

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.METADATA_ONLY})
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

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.EMBED_REPLACE})
        self.assertEqual(report.embedding_calls, 1)

    def test_a_missing_manifest_is_repaired_without_embedding(self):
        self._sync()
        es_client().delete(index=self.index, id=manifest_id(self.identity), refresh=True)

        report = self._sync()

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.COMMIT_REPAIR})
        self.assertEqual(report.embedding_calls, 0)
        self.assertIsNotNone(self._stored_state().manifest)

    def test_an_ineligible_document_is_evicted(self):
        self._sync()
        self.document.restrict_to_groups.add(GroupFactory())

        with self.assertLogs("k.retrieval", level="INFO") as logs:
            report = self._sync()

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.DELETED})
        self.assertEqual(logs.records[0].outcomes, {self.index: "deleted"})
        stored = self._stored_state()
        self.assertEqual(stored.chunks, [])
        self.assertIsNone(stored.manifest)

    def test_a_deleted_row_is_evicted_by_object(self):
        self._sync()
        document_id = self.document.id
        self.document.delete()

        report = sync_document_chunks(document_id)

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.DELETED})
        self.assertEqual(self._stored_state().chunks, [])

    def test_delete_document_chunks_removes_everything(self):
        self._sync()

        report = delete_document_chunks(self.identity)

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.DELETED})
        stored = self._stored_state()
        self.assertEqual(stored.chunks, [])
        self.assertIsNone(stored.manifest)

    def test_an_explicit_target_does_not_fan_out(self):
        report = self._sync(target_indexes=[self.index])
        self.assertEqual(list(report.outcomes), [self.index])

    def test_no_active_target_writes_nothing(self):
        with self.assertLogs("k.retrieval", level="WARNING") as logs:
            report = self._sync(target_indexes=[])
        self.assertEqual(report.outcomes, {})
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

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.ABORTED_STALE})
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
        self.assertEqual(report.outcomes, {self.index: SyncOutcome.ABORTED_STALE})
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

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.DELETED})
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

        self.assertEqual(report.outcomes, {self.index: SyncOutcome.ABORTED_STALE})
        self.assertEqual(report.embedding_calls, 0)

    def test_the_completion_event_carries_no_text_or_vectors(self):
        with self.assertLogs("k.retrieval", level="INFO") as logs:
            self._sync()
        [record] = logs.records
        self.assertEqual(record.getMessage(), "retrieval.sync.completed")
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


class MultiGenerationTests(ChunkIndexTestCase):
    """Fan-out across a migration window, where read and write aliases differ."""

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

    def test_divergent_targets_both_receive_the_document_from_one_call(self):
        second = self._second_generation()

        report = sync_document_chunks(self.document.id)

        self.assertEqual(set(report.outcomes), {self.first, second})
        # Both generations share an embedding fingerprint, so the provider is paid once.
        self.assertEqual(report.embedding_calls, 1)
        for index in (self.first, second):
            stored = read_indexed_document(index=index, identity=self.identity)
            self.assertGreater(len(stored.chunks), 0)
            self.assertIsNotNone(stored.manifest)

    def test_divergent_embedding_profiles_do_not_share_a_call(self):
        other_space = EmbeddingRecipe(
            **{**recipe_to_payload(configured_embedding_recipe()), "model": "another-model"}
        )
        second = self._second_generation(other_space)

        report = sync_document_chunks(self.document.id)

        self.assertEqual(set(report.outcomes), {self.first, second})
        # A model migration is exactly the case that needs one call per vector space.
        self.assertEqual(report.embedding_calls, 2)

    def test_a_newer_state_in_one_target_aborts_every_target(self):
        expected = _expected(
            chunk("kb", self.document.html, title=self.document.title),
            build_source(self.document),
            indexed_revision_id=self.document.current_revision_id + 1,
        )
        commit_manifest(index=self.first, identity=self.identity, expected_state=expected)
        second = self._second_generation()

        report = sync_document_chunks(self.document.id)

        self.assertEqual(
            report.outcomes,
            dict.fromkeys((self.first, second), SyncOutcome.ABORTED_STALE),
        )
        self.assertEqual(report.embedding_calls, 0)
        self.assertEqual(read_indexed_document(index=second, identity=self.identity).chunks, [])


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

    def test_a_document_with_no_chunkable_content_commits_an_empty_manifest(self):
        Document.objects.filter(pk=self.document.id).update(html="")

        report = sync_document_chunks(self.document.id)

        stored = self._stored()
        self.assertEqual(stored.chunks, [])
        # "Processed and empty" has to be distinguishable from "never processed".
        self.assertIsNotNone(stored.manifest)
        self.assertEqual(stored.manifest.chunk_count, 0)
        # There is nothing to embed, so the only outstanding work is the manifest itself.
        self.assertEqual(report.outcomes, {self.index: SyncOutcome.COMMIT_REPAIR})
        self.assertEqual(report.embedding_calls, 0)
