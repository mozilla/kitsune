from unittest import mock

from django.test import SimpleTestCase

from kitsune.retrieval.chunking import CHUNKING_GENERATION, chunk
from kitsune.retrieval.embeddings import configured_embedding_recipe
from kitsune.retrieval.gate import (
    GateCategory,
    gate_index,
    verify_indexed_document,
)
from kitsune.retrieval.index import (
    VECTOR_DIMS,
    ChunkDocument,
    ChunkIdentity,
    IndexedDocumentState,
    chunk_id,
    commit_manifest,
    delete_chunk_positions,
    manifest_id,
)
from kitsune.retrieval.sync import SyncOutcome, build_source, sync_document_chunks
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.retrieval.tests.test_index import _expected, _source
from kitsune.retrieval.tests.test_sync import _chunks, _stored
from kitsune.search.es_utils import es_client
from kitsune.users.tests import GroupFactory
from kitsune.wiki.models import Document
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _indexed(chunks, source, state, *, manifest=..., extra_positions=(), **overrides):
    documents = _stored(chunks, source, state, **overrides)
    for position in extra_positions:
        documents.append(dict(documents[0], position=position))
    return IndexedDocumentState(
        manifest=state if manifest is ... else manifest,
        chunks=sorted(documents, key=lambda item: item["position"]),
    )


def _verify(chunks, source, state, indexed, recipe=None):
    return verify_indexed_document(
        chunks=chunks,
        source=source,
        expected_state=state,
        indexed=indexed,
        recipe=recipe or configured_embedding_recipe(),
    )


def _categories(findings):
    return {finding.category for finding in findings}


class VerifyDocumentTests(SimpleTestCase):
    """The defect matrix is pure: expected state plus indexed state names every finding, with
    no Elasticsearch, Redis, or database access."""

    def setUp(self):
        self.source = _source()
        self.chunks = _chunks(3)
        self.state = _expected(self.chunks, self.source)

    def test_a_fully_committed_document_has_no_findings(self):
        indexed = _indexed(self.chunks, self.source, self.state)
        self.assertEqual(_verify(self.chunks, self.source, self.state, indexed), ())

    def test_a_committed_zero_chunk_document_is_complete(self):
        empty = _chunks(0)
        state = _expected(empty, self.source)
        indexed = IndexedDocumentState(manifest=state, chunks=[])
        self.assertEqual(_verify(empty, self.source, state, indexed), ())

    def test_nothing_indexed_is_a_missing_document(self):
        indexed = IndexedDocumentState(manifest=None, chunks=[])
        self.assertEqual(
            _categories(_verify(self.chunks, self.source, self.state, indexed)),
            {GateCategory.MISSING_DOCUMENT},
        )

    def test_chunks_without_a_manifest_are_an_incomplete_commit(self):
        indexed = _indexed(self.chunks, self.source, self.state, manifest=None)
        self.assertIn(
            GateCategory.MISSING_MANIFEST,
            _categories(_verify(self.chunks, self.source, self.state, indexed)),
        )

    def test_a_manifest_disagreeing_with_the_database_is_stale(self):
        for field, value in (
            ("indexed_revision_id", 999),
            ("chunking_generation", CHUNKING_GENERATION + 1),
            ("chunk_count", 2),
            ("content_hash", "0" * 64),
            ("index_state_hash", "0" * 64),
        ):
            with self.subTest(field=field):
                stored = _expected(self.chunks, self.source, **{field: value})
                indexed = _indexed(self.chunks, self.source, self.state, manifest=stored)
                self.assertIn(
                    GateCategory.STALE_MANIFEST,
                    _categories(_verify(self.chunks, self.source, self.state, indexed)),
                )

    def test_a_missing_position_is_a_gap(self):
        indexed = _indexed(self.chunks, self.source, self.state, count=2)
        self.assertIn(
            GateCategory.POSITION_GAP,
            _categories(_verify(self.chunks, self.source, self.state, indexed)),
        )

    def test_positions_beyond_the_expected_range_are_orphans(self):
        indexed = _indexed(self.chunks, self.source, self.state, extra_positions=(3, 7))
        findings = _verify(self.chunks, self.source, self.state, indexed)
        self.assertIn(GateCategory.ORPHAN_CHUNK, _categories(findings))

    def test_duplicate_positions_are_orphans(self):
        indexed = _indexed(self.chunks, self.source, self.state)
        indexed.chunks.append(dict(indexed.chunks[0]))
        self.assertIn(
            GateCategory.ORPHAN_CHUNK,
            _categories(_verify(self.chunks, self.source, self.state, indexed)),
        )

    def test_an_unusable_vector_is_reported(self):
        for vector in ([], [0.0] * (VECTOR_DIMS - 1), [float("nan")] * VECTOR_DIMS, None, "vec"):
            with self.subTest(vector=vector):
                indexed = _indexed(self.chunks, self.source, self.state, content_vector=vector)
                self.assertIn(
                    GateCategory.INVALID_VECTOR,
                    _categories(_verify(self.chunks, self.source, self.state, indexed)),
                )

    def test_chunk_state_disagreeing_with_the_manifest_is_reported(self):
        for field in ("content_hash", "index_state_hash"):
            with self.subTest(field=field):
                indexed = _indexed(self.chunks, self.source, self.state, **{field: "0" * 64})
                self.assertIn(
                    GateCategory.STALE_CHUNK_STATE,
                    _categories(_verify(self.chunks, self.source, self.state, indexed)),
                )

    def test_a_mixed_chunking_generation_across_chunks_is_reported(self):
        # A partially replaced document is the shape a crashed writer leaves behind.
        documents = _stored(self.chunks, self.source, self.state)
        documents[1]["chunking_generation"] = CHUNKING_GENERATION + 1
        indexed = IndexedDocumentState(manifest=self.state, chunks=documents)
        self.assertIn(
            GateCategory.STALE_CHUNK_STATE,
            _categories(_verify(self.chunks, self.source, self.state, indexed)),
        )

    def test_stored_text_that_is_not_the_expected_chunk_is_reported(self):
        indexed = _indexed(
            _chunks(3, text="old {i}"), self.source, self.state, manifest=self.state
        )
        self.assertIn(
            GateCategory.STALE_CHUNK_STATE,
            _categories(_verify(self.chunks, self.source, self.state, indexed)),
        )

    def test_a_restricted_document_indexed_at_all_is_access_drift(self):
        restricted = _source(visibility="group_restricted", access_group_ids=[4])
        state = _expected(self.chunks, restricted)
        indexed = _indexed(self.chunks, restricted, state)
        self.assertIn(
            GateCategory.ACCESS_DRIFT,
            _categories(_verify(self.chunks, restricted, state, indexed)),
        )

    def test_stored_access_metadata_disagreeing_with_the_database_is_access_drift(self):
        indexed = _indexed(
            self.chunks,
            self.source,
            self.state,
            visibility="group_restricted",
            access_group_ids=[7],
        )
        self.assertIn(
            GateCategory.ACCESS_DRIFT,
            _categories(_verify(self.chunks, self.source, self.state, indexed)),
        )

    def test_access_drift_is_reported_even_when_every_hash_is_current(self):
        # Otherwise a stale access set hides behind an otherwise healthy document.
        indexed = _indexed(self.chunks, self.source, self.state, visibility="group_restricted")
        findings = _verify(self.chunks, self.source, self.state, indexed)
        self.assertEqual(_categories(findings), {GateCategory.ACCESS_DRIFT})

    def test_no_finding_carries_text_vectors_or_group_ids(self):
        indexed = _indexed(
            self.chunks,
            self.source,
            self.state,
            content_vector=[float("nan")] * VECTOR_DIMS,
            visibility="group_restricted",
            access_group_ids=[31337],
        )
        rendered = repr(_verify(self.chunks, self.source, self.state, indexed))
        for secret in ("31337", "body 0", "nan"):
            self.assertNotIn(secret, rendered)

    def test_invalid_bounds_fail_before_enumeration(self):
        for options in ({"page_size": 0}, {"max_findings": -1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                gate_index("unused", **options)


class GateIndexTestCase(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        self.document = self._document("Install Firefox", "install-firefox")
        self.identity = ChunkIdentity("kb", str(self.document.id), self.document.locale)

    def _document(self, title, slug, locale="en-US", parent=None):
        document = DocumentFactory(title=title, slug=slug, locale=locale, parent=parent)
        ApprovedRevisionFactory(document=document, summary=f"{title} summary")
        document.refresh_from_db()
        return document


class GateEnumerationTests(GateIndexTestCase):
    """The gate against real Elasticsearch: what the database expects versus what is stored."""

    def test_a_synced_corpus_passes_cleanly(self):
        sync_document_chunks(self.document.id)

        report = gate_index(self.index)

        self.assertTrue(report.is_clean)
        self.assertEqual(report.counts, {})
        self.assertEqual(report.documents_checked, 1)
        self.assertEqual(report.identities_indexed, 1)
        self.assertEqual(report.stale_document_ids, ())
        self.assertEqual(report.unexpected_identities, ())

    def test_an_unindexed_eligible_document_is_reported_and_named_for_sync(self):
        report = gate_index(self.index)

        self.assertFalse(report.is_clean)
        self.assertEqual(report.counts, {GateCategory.MISSING_DOCUMENT.value: 1})
        self.assertEqual(report.stale_document_ids, (self.document.id,))

    def test_a_deleted_row_still_indexed_is_named_for_deletion(self):
        sync_document_chunks(self.document.id)
        Document.objects.filter(pk=self.document.id).delete()

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.DELETED_IDENTITY.value: 1})
        self.assertEqual(report.unexpected_identities, (self.identity,))
        self.assertEqual(report.stale_document_ids, ())

    def test_an_ineligible_row_still_indexed_is_named_for_deletion(self):
        sync_document_chunks(self.document.id)
        Document.objects.filter(pk=self.document.id).update(is_archived=True)

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.INELIGIBLE_IDENTITY.value: 1})
        self.assertEqual(report.unexpected_identities, (self.identity,))

    def test_a_restricted_document_left_in_the_index_is_access_drift_not_generic_staleness(self):
        sync_document_chunks(self.document.id)
        self.document.restrict_to_groups.add(GroupFactory())

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.ACCESS_DRIFT.value: 1})
        self.assertEqual(report.unexpected_identities, (self.identity,))

    def test_access_drift_with_a_current_hash_is_selected_and_repaired_without_embedding(self):
        sync_document_chunks(self.document.id)
        es_client().update(
            index=self.index,
            id=chunk_id(self.identity, 0),
            doc={"visibility": "group_restricted", "access_group_ids": [31337]},
            refresh=True,
        )

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.ACCESS_DRIFT.value: 1})
        self.assertEqual(report.stale_document_ids, (self.document.id,))
        with mock.patch("kitsune.retrieval.sync.get_embeddings") as embed:
            sync_report = sync_document_chunks(self.document.id)
        embed.assert_not_called()
        self.assertEqual(sync_report.outcomes, {self.index: SyncOutcome.METADATA_ONLY})
        self.assertTrue(gate_index(self.index).is_clean)

    def test_a_stale_manifest_is_reported_and_named_for_sync(self):
        sync_document_chunks(self.document.id)
        commit_manifest(
            index=self.index,
            identity=self.identity,
            expected_state=_expected(
                chunk("kb", self.document.html, title=self.document.title),
                build_source(self.document),
                indexed_revision_id=self.document.current_revision_id - 1,
            ),
        )

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.STALE_MANIFEST.value: 1})
        self.assertEqual(report.stale_document_ids, (self.document.id,))

    def test_a_missing_chunk_is_reported_as_a_gap(self):
        sync_document_chunks(self.document.id)
        delete_chunk_positions(index=self.index, identity=self.identity, positions=(0,))

        report = gate_index(self.index)

        self.assertIn(GateCategory.POSITION_GAP.value, report.counts)
        self.assertEqual(report.stale_document_ids, (self.document.id,))

    def test_a_missing_manifest_is_reported(self):
        sync_document_chunks(self.document.id)
        es_client().delete(index=self.index, id=manifest_id(self.identity), refresh=True)

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.MISSING_MANIFEST.value: 1})
        self.assertEqual(report.stale_document_ids, (self.document.id,))

    def test_the_gate_writes_nothing(self):
        sync_document_chunks(self.document.id)
        Document.objects.filter(pk=self.document.id).update(is_archived=True)
        before = es_client().count(index=self.index)["count"]

        gate_index(self.index)

        self.assertEqual(es_client().count(index=self.index)["count"], before)

    def test_more_documents_than_one_result_page_are_all_checked(self):
        for number in range(7):
            self._document(f"Article {number}", f"article-{number}")

        report = gate_index(self.index, page_size=2)

        self.assertEqual(report.documents_checked, 8)
        self.assertEqual(report.counts, {GateCategory.MISSING_DOCUMENT.value: 8})

    def test_a_locale_filter_narrows_both_sides(self):
        translation = self._document("Firefox installieren", "de-install", "de", self.document)
        sync_document_chunks(self.document.id)
        sync_document_chunks(translation.id)

        report = gate_index(self.index, locales=["de"])

        self.assertTrue(report.is_clean)
        self.assertEqual(report.documents_checked, 1)
        self.assertEqual(report.identities_indexed, 1)

    def test_the_reported_findings_are_bounded_but_the_counts_are_exact(self):
        for number in range(3):
            self._document(f"Article {number}", f"article-{number}")

        report = gate_index(self.index, max_findings=2)

        self.assertEqual(len(report.findings), 2)
        self.assertEqual(report.findings_omitted, 2)
        self.assertEqual(report.counts, {GateCategory.MISSING_DOCUMENT.value: 4})

    def test_an_orphan_chunk_beyond_the_expected_count_is_reported(self):
        sync_document_chunks(self.document.id)
        # Copy a healthy chunk to a position the document no longer has: what a writer that
        # died between replacing chunks and pruning leftovers leaves behind.
        healthy = es_client().get(index=self.index, id=chunk_id(self.identity, 0))["_source"]
        es_client().index(
            index=self.index,
            id=chunk_id(self.identity, 99),
            document={**healthy, "position": 99},
            refresh=True,
        )

        report = gate_index(self.index)

        self.assertIn(GateCategory.ORPHAN_CHUNK.value, report.counts)
        self.assertEqual(report.stale_document_ids, (self.document.id,))

    def test_the_gate_event_reports_counts_without_sensitive_payloads(self):
        sync_document_chunks(self.document.id)
        self.document.restrict_to_groups.add(GroupFactory())

        with self.assertLogs("k.retrieval", level="INFO") as logs:
            gate_index(self.index)

        [record] = [r for r in logs.records if r.getMessage() == "retrieval.gate.completed"]
        self.assertEqual(record.index, self.index)
        self.assertEqual(record.clean, False)
        self.assertNotIn("Install Firefox", repr(record.__dict__))
        for field in ("content_text", "content_vector", "access_group_ids", "title"):
            self.assertNotIn(field, record.__dict__)
