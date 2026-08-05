from unittest import mock

from django.test import SimpleTestCase
from elasticsearch.helpers import scan

from kitsune.retrieval.chunking import CHUNKING_GENERATION, chunk
from kitsune.retrieval.embeddings import get_embeddings
from kitsune.retrieval.gate import (
    GateCategory,
    gate_index,
    verify_indexed_document,
)
from kitsune.retrieval.index import (
    ChunkDocument,
    ChunkIdentity,
    IndexedDocumentSummary,
    StoredChunkSummary,
    chunk_id,
    commit_manifest,
    manifest_id,
)
from kitsune.retrieval.sync import SyncOutcome, build_source, sync_document_chunks
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.retrieval.tests.test_index import _expected, _source
from kitsune.retrieval.tests.test_sync import _chunks
from kitsune.search.es_utils import es_client
from kitsune.users.tests import GroupFactory
from kitsune.wiki.models import Document
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


def _indexed(chunks, source, state, *, manifest=..., positions=None):
    if positions is None:
        positions = range(len(chunks))
    summaries = tuple(
        StoredChunkSummary(
            position,
            source.visibility,
            source.access_group_ids,
        )
        for position in positions
    )
    return IndexedDocumentSummary(
        manifest=state if manifest is ... else manifest,
        chunks=summaries,
    )


def _verify(source, state, indexed):
    return verify_indexed_document(
        source=source,
        expected_state=state,
        indexed=indexed,
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
        self.assertEqual(_verify(self.source, self.state, indexed), ())

    def test_a_committed_zero_chunk_document_is_complete(self):
        empty = _chunks(0)
        state = _expected(empty, self.source)
        indexed = IndexedDocumentSummary(manifest=state, chunks=())
        self.assertEqual(_verify(self.source, state, indexed), ())

    def test_a_missing_manifest_is_a_stale_document(self):
        for positions in ((), range(len(self.chunks))):
            with self.subTest(positions=positions):
                indexed = _indexed(
                    self.chunks, self.source, self.state, manifest=None, positions=positions
                )
                self.assertEqual(
                    _categories(_verify(self.source, self.state, indexed)),
                    {GateCategory.STALE_DOCUMENT},
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
                    GateCategory.STALE_DOCUMENT,
                    _categories(_verify(self.source, self.state, indexed)),
                )

    def test_missing_extra_duplicate_or_malformed_positions_are_layout_mismatches(self):
        for positions in ((0, 1), (0, 1, 2, 7), (0, 1, 1), (0, 1, None)):
            with self.subTest(positions=positions):
                indexed = _indexed(self.chunks, self.source, self.state, positions=positions)
                self.assertEqual(
                    _categories(_verify(self.source, self.state, indexed)),
                    {GateCategory.CHUNK_LAYOUT_MISMATCH},
                )

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

    def test_the_corpus_is_read_by_one_bounded_elasticsearch_scan(self):
        sync_document_chunks(self.document.id)

        with mock.patch("kitsune.retrieval.index.scan", wraps=scan) as index_scan:
            self.assertTrue(gate_index(self.index).is_clean)

        index_scan.assert_called_once()
        source_fields = index_scan.call_args.kwargs["query"]["_source"]
        self.assertNotIn("content_text", source_fields)
        self.assertNotIn("content_vector", source_fields)

    def test_an_unindexed_eligible_document_is_reported_and_named_for_sync(self):
        report = gate_index(self.index)

        self.assertFalse(report.is_clean)
        self.assertEqual(report.counts, {GateCategory.STALE_DOCUMENT.value: 1})
        self.assertEqual(report.stale_document_ids, (self.document.id,))

    def test_a_deleted_row_still_indexed_is_named_for_deletion(self):
        sync_document_chunks(self.document.id)
        Document.objects.filter(pk=self.document.id).delete()

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.UNEXPECTED_IDENTITY.value: 1})
        self.assertEqual(report.unexpected_identities, (self.identity,))
        self.assertEqual(report.stale_document_ids, ())

    def test_an_ineligible_row_still_indexed_is_named_for_deletion(self):
        sync_document_chunks(self.document.id)
        Document.objects.filter(pk=self.document.id).update(is_archived=True)

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.UNEXPECTED_IDENTITY.value: 1})
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
        self.assertEqual(sync_report.outcome, SyncOutcome.METADATA_ONLY)
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

        self.assertEqual(report.counts, {GateCategory.STALE_DOCUMENT.value: 1})
        self.assertEqual(report.stale_document_ids, (self.document.id,))

    def test_a_missing_chunk_is_reported_as_a_gap(self):
        sync_document_chunks(self.document.id)
        es_client().delete(index=self.index, id=chunk_id(self.identity, 0), refresh=True)

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.CHUNK_LAYOUT_MISMATCH.value: 1})
        self.assertEqual(report.stale_document_ids, (self.document.id,))

        with mock.patch("kitsune.retrieval.sync.get_embeddings", wraps=get_embeddings) as embed:
            sync_report = sync_document_chunks(self.document.id)
        self.assertEqual(sync_report.outcome, SyncOutcome.EMBED_REPLACE)
        embed.assert_called_once()
        self.assertTrue(gate_index(self.index).is_clean)

    def test_a_missing_manifest_is_reported(self):
        sync_document_chunks(self.document.id)
        es_client().delete(index=self.index, id=manifest_id(self.identity), refresh=True)

        report = gate_index(self.index)

        self.assertEqual(report.counts, {GateCategory.STALE_DOCUMENT.value: 1})
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
        self.assertEqual(report.counts, {GateCategory.STALE_DOCUMENT.value: 8})

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
        self.assertEqual(report.counts, {GateCategory.STALE_DOCUMENT.value: 4})

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
