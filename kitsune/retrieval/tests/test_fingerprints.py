"""Tests for canonical serialization, document hashes, and index fingerprints."""

import hashlib
import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace

from django.test import SimpleTestCase
from elasticsearch import NotFoundError

from kitsune.retrieval.chunking import Chunk
from kitsune.retrieval.embeddings import EmbeddingRecipe
from kitsune.retrieval.fingerprints import (
    IndexMetaAction,
    InvalidIndexMeta,
    build_index_meta,
    canonical_json,
    classify_meta_mismatch,
    content_hash,
    document_embedding_fingerprint,
    index_state_hash,
    mapping_fingerprint,
    query_embedding_fingerprint,
    read_index_meta,
    scope_envelope,
    write_index_meta,
)
from kitsune.search.es_utils import es_client
from kitsune.search.tests import ElasticTestCase

RECIPE = EmbeddingRecipe(
    provider="fake",
    model="text-embedding-005",
    dimensions=768,
    document_task="RETRIEVAL_DOCUMENT",
    query_task="RETRIEVAL_QUERY",
    normalization="none",
)
INDEX_OPTIONS = {"type": "hnsw", "m": 16, "ef_construction": 100}


def _chunk(text="body", position=0, heading_path="Title > H", scope=()):
    return Chunk(text=text, position=position, heading_path=heading_path, scope=scope)


def _source(**overrides):
    fields = {
        "title": "Title",
        "summary": "Summary",
        "keywords": "kw",
        "slug": "slug",
        "category": "10",
        "product_ids": ["1", "2"],
        "topic_ids": ["3", "4"],
        "family_id": "42",
        "updated": datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC),
        "visibility": "public",
        "access_group_ids": [],
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


def _meta(recipe=RECIPE, *, similarity="cosine", index_options=None, schema_version=1):
    return build_index_meta(
        recipe,
        similarity=similarity,
        index_options=index_options or INDEX_OPTIONS,
        schema_version=schema_version,
    )


def _redigest(block):
    payload = {key: value for key, value in block.items() if key != "digest"}
    block["digest"] = hashlib.sha256(canonical_json(payload)).hexdigest()


class CanonicalJsonTests(SimpleTestCase):
    def test_sorts_object_keys_without_reordering_lists(self):
        left = canonical_json({"x": [3, 1, 2], "y": {"b": 1, "a": 2}})
        right = canonical_json({"y": {"a": 2, "b": 1}, "x": [3, 1, 2]})
        self.assertEqual(left, right)
        self.assertEqual(left, b'{"x":[3,1,2],"y":{"a":2,"b":1}}')


class ScopeEnvelopeTests(SimpleTestCase):
    def test_encodes_empty_scope_and_preserves_clause_order(self):
        self.assertEqual(scope_envelope(()), {"version": 1, "clauses": []})
        self.assertEqual(
            scope_envelope((frozenset({"win", "mac"}), frozenset({"fx"}))),
            {"version": 1, "clauses": [["mac", "win"], ["fx"]]},
        )


class ContentHashTests(SimpleTestCase):
    def test_is_a_stable_hex_digest(self):
        digest = content_hash([_chunk(text="a"), _chunk(text="b", position=1)])
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, content_hash([_chunk(text="a"), _chunk(text="b", position=1)]))

    def test_chunk_order_matters(self):
        a = content_hash([_chunk(text="a", position=0), _chunk(text="b", position=1)])
        b = content_hash([_chunk(text="b", position=0), _chunk(text="a", position=1)])
        self.assertNotEqual(a, b)

    def test_only_text_participates(self):
        # Different heading_path/scope, identical text → identical content hash.
        a = content_hash([_chunk(text="same", heading_path="H1", scope=())])
        b = content_hash([_chunk(text="same", heading_path="H2", scope=(frozenset({"win"}),))])
        self.assertEqual(a, b)


class IndexStateHashTests(SimpleTestCase):
    def test_excludes_chunk_text(self):
        a = index_state_hash([_chunk(text="one")], _source())
        b = index_state_hash([_chunk(text="two")], _source())
        self.assertEqual(a, b)

    def test_heading_path_participates(self):
        a = index_state_hash([_chunk(heading_path="H1")], _source())
        b = index_state_hash([_chunk(heading_path="H2")], _source())
        self.assertNotEqual(a, b)

    def test_outer_scope_clause_order_changes_hash(self):
        ab = index_state_hash([_chunk(scope=(frozenset({"win"}), frozenset({"fx"})))], _source())
        ba = index_state_hash([_chunk(scope=(frozenset({"fx"}), frozenset({"win"})))], _source())
        self.assertNotEqual(ab, ba)

    def test_unordered_id_collections_are_stable_under_reordering(self):
        a = index_state_hash(
            [_chunk()],
            _source(product_ids=["1", "2"], topic_ids=["3", "4"], access_group_ids=[7, 9]),
        )
        b = index_state_hash(
            [_chunk()],
            _source(product_ids=["2", "1"], topic_ids=["4", "3"], access_group_ids=[9, 7]),
        )
        self.assertEqual(a, b)

    def test_access_group_change_flips_hash(self):
        a = index_state_hash(
            [_chunk()], _source(visibility="group_restricted", access_group_ids=[7])
        )
        b = index_state_hash(
            [_chunk()], _source(visibility="group_restricted", access_group_ids=[8])
        )
        self.assertNotEqual(a, b)

    def test_visibility_change_flips_hash(self):
        a = index_state_hash([_chunk()], _source(visibility="public"))
        b = index_state_hash([_chunk()], _source(visibility="group_restricted"))
        self.assertNotEqual(a, b)

    def test_timestamp_same_instant_different_zone_is_stable(self):
        utc = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC)
        plus2 = datetime(2026, 7, 28, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))
        self.assertEqual(
            index_state_hash([_chunk()], _source(updated=utc)),
            index_state_hash([_chunk()], _source(updated=plus2)),
        )

    def test_subsecond_timestamp_change_flips_hash(self):
        a = index_state_hash(
            [_chunk()],
            _source(updated=datetime(2026, 7, 28, 12, 0, 0, 100_000, tzinfo=UTC)),
        )
        b = index_state_hash(
            [_chunk()],
            _source(updated=datetime(2026, 7, 28, 12, 0, 0, 900_000, tzinfo=UTC)),
        )
        self.assertNotEqual(a, b)

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            index_state_hash([_chunk()], _source(updated=datetime(2026, 7, 28, 12, 0, 0)))

    def test_summary_change_flips_hash(self):
        a = index_state_hash([_chunk()], _source(summary="one"))
        b = index_state_hash([_chunk()], _source(summary="two"))
        self.assertNotEqual(a, b)


class EmbeddingFingerprintTests(SimpleTestCase):
    def test_returns_readable_payload_and_hex_digest(self):
        payload, digest = document_embedding_fingerprint(RECIPE)
        self.assertEqual(payload["model"], "text-embedding-005")
        self.assertEqual(payload["dimensions"], 768)
        self.assertEqual(len(digest), 64)

    def test_task_types_only_affect_their_own_fingerprint(self):
        _, before = document_embedding_fingerprint(RECIPE)
        _, after = document_embedding_fingerprint(replace(RECIPE, query_task="OTHER"))
        self.assertEqual(before, after)

        _, before = query_embedding_fingerprint(RECIPE)
        _, after = query_embedding_fingerprint(replace(RECIPE, document_task="OTHER"))
        self.assertEqual(before, after)

        _, before = document_embedding_fingerprint(RECIPE)
        _, after = document_embedding_fingerprint(replace(RECIPE, document_task="OTHER"))
        self.assertNotEqual(before, after)

    def test_model_or_dims_change_flips_both(self):
        _, doc_before = document_embedding_fingerprint(RECIPE)
        _, query_before = query_embedding_fingerprint(RECIPE)
        changed = replace(RECIPE, dimensions=512)
        self.assertNotEqual(doc_before, document_embedding_fingerprint(changed)[1])
        self.assertNotEqual(query_before, query_embedding_fingerprint(changed)[1])


class MappingFingerprintTests(SimpleTestCase):
    def test_payload_does_not_alias_mutable_index_options(self):
        index_options = dict(INDEX_OPTIONS)
        payload, _ = mapping_fingerprint(
            dims=768,
            similarity="cosine",
            index_options=index_options,
            schema_version=1,
        )

        payload["index_options"]["m"] = 32

        self.assertEqual(index_options["m"], 16)

    def test_changes_only_for_its_inputs(self):
        _, base = mapping_fingerprint(
            dims=768, similarity="cosine", index_options=INDEX_OPTIONS, schema_version=1
        )
        self.assertEqual(
            base,
            mapping_fingerprint(
                dims=768, similarity="cosine", index_options=INDEX_OPTIONS, schema_version=1
            )[1],
        )
        for changed in (
            {"dims": 512},
            {"similarity": "dot_product"},
            {"index_options": {"type": "hnsw", "m": 32, "ef_construction": 100}},
            {"schema_version": 2},
        ):
            kwargs = {
                "dims": 768,
                "similarity": "cosine",
                "index_options": INDEX_OPTIONS,
                "schema_version": 1,
                **changed,
            }
            self.assertNotEqual(base, mapping_fingerprint(**kwargs)[1])


class ClassifyMismatchTests(SimpleTestCase):
    def test_selects_the_cheapest_safe_action(self):
        cases = (
            ("unchanged", _meta(), IndexMetaAction.NONE),
            (
                "query recipe",
                _meta(replace(RECIPE, query_task="OTHER")),
                IndexMetaAction.QUERY_META_UPDATE,
            ),
            ("mapping", _meta(schema_version=2), IndexMetaAction.REBUILD),
            (
                "embedding",
                _meta(replace(RECIPE, model="other-model")),
                IndexMetaAction.REBUILD,
            ),
        )
        for reason, desired, expected in cases:
            with self.subTest(reason=reason):
                self.assertEqual(classify_meta_mismatch(_meta(), desired), expected)

    def test_dimensions_change_reembeds_even_when_mapping_also_differs(self):
        # A dims change flips embedding *and* mapping fingerprints; document precedence wins.
        desired = build_index_meta(
            replace(RECIPE, dimensions=512),
            similarity="cosine",
            index_options=INDEX_OPTIONS,
            schema_version=1,
        )
        self.assertEqual(classify_meta_mismatch(_meta(), desired), IndexMetaAction.REBUILD)


class IndexMetaIoTests(ElasticTestCase):
    """`read`/`write_index_meta` against a concrete index, with fail-closed re-validation."""

    def setUp(self):
        super().setUp()
        # Keep this outside ChunkDocument's wildcard and unique per parallel test process.
        self.index = f"retrieval_fingerprint_meta_io_{os.getpid()}"
        self._drop_index()
        es_client().indices.create(index=self.index)

    def tearDown(self):
        self._drop_index()
        super().tearDown()

    def _drop_index(self):
        # ignore_unavailable only suppresses wildcard misses; an exact missing index still
        # 404s on ES 9.x, so ignore NotFoundError explicitly (as search/base.py does).
        try:
            es_client().indices.delete(index=self.index)
        except NotFoundError:
            pass

    def write_raw_meta(self, meta):
        """Bypass the validated application writer to simulate damaged stored `_meta`."""
        es_client().indices.put_mapping(index=self.index, meta=meta)

    def test_write_then_read_round_trips(self):
        meta = _meta()
        write_index_meta(self.index, meta)
        self.assertEqual(read_index_meta(self.index), meta)

    def test_absent_meta_fails_closed(self):
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_missing_section_fails_closed(self):
        incomplete = _meta()
        del incomplete["mapping"]
        self.write_raw_meta(incomplete)
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_missing_digest_fails_closed(self):
        incomplete = _meta()
        del incomplete["query"]["digest"]
        self.write_raw_meta(incomplete)
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_corrupt_digest_fails_closed(self):
        corrupt = _meta()
        corrupt["mapping"]["digest"] = "0" * 64
        self.write_raw_meta(corrupt)
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_tampered_payload_fails_closed(self):
        tampered = _meta()
        tampered["embedding"]["model"] = "swapped-out-model"  # digest not recomputed
        self.write_raw_meta(tampered)
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_self_consistent_but_missing_field_fails_closed(self):
        malformed = _meta()
        del malformed["embedding"]["provider"]
        _redigest(malformed["embedding"])
        self.write_raw_meta(malformed)
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_inconsistent_recipe_dimensions_fail_closed(self):
        malformed = _meta()
        malformed["query"]["dimensions"] = 512
        _redigest(malformed["query"])
        self.write_raw_meta(malformed)
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_malformed_index_options_fail_closed(self):
        malformed = _meta()
        malformed["mapping"]["index_options"]["m"] = "16"
        _redigest(malformed["mapping"])
        self.write_raw_meta(malformed)
        with self.assertRaises(InvalidIndexMeta):
            read_index_meta(self.index)

    def test_application_writer_rejects_invalid_meta(self):
        malformed = _meta()
        del malformed["mapping"]
        with self.assertRaises(InvalidIndexMeta):
            write_index_meta(self.index, malformed)
