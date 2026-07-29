from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase

from kitsune.retrieval.chunking import CHUNKING_GENERATION, Chunk, chunk_kb
from kitsune.retrieval.fingerprints import content_hash, index_state_hash, scope_envelope
from kitsune.retrieval.index import (
    ChunkDocument,
    ChunkIdentity,
    ChunkSource,
    ExpectedDocumentState,
    InvalidDocumentState,
    chunk_id,
    delete_chunks_for,
    index_chunks,
    manifest_doc,
    manifest_id,
    parse_manifest,
)
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.search.es_utils import es_client


def _source(**overrides):
    fields = {
        "content_type": "kb",
        "object_id": "1",
        "locale": "en-US",
        "family_id": "1",
        "title": "Install Firefox",
        "summary": "How to install Firefox.",
        "keywords": "install setup",
        "slug": "install-firefox",
        "category": "10",
        "product_ids": ["3"],
        "topic_ids": ["10"],
        "visibility": "public",
        "access_group_ids": [],
        "updated": datetime(2026, 1, 1, tzinfo=UTC),
    }
    fields.update(overrides)
    return ChunkSource(**fields)


def _state(**overrides):
    fields = {
        "content_hash": "a" * 64,
        "index_state_hash": "b" * 64,
        "chunking_generation": CHUNKING_GENERATION,
        "chunk_count": 3,
        "indexed_revision_id": 42,
        "updated": datetime(2026, 1, 1, tzinfo=UTC),
    }
    fields.update(overrides)
    return ExpectedDocumentState(**fields)


class IdentityAndIdTests(SimpleTestCase):
    def test_chunk_source_exposes_its_identity(self):
        self.assertEqual(_source().identity, ChunkIdentity("kb", "1", "en-US"))

    def test_deterministic_chunk_and_manifest_ids(self):
        identity = ChunkIdentity("kb", "42", "de")
        self.assertEqual(chunk_id(identity, 3), "kb:42:de:3")
        self.assertEqual(manifest_id(identity), "kb:42:de:manifest")

    def test_value_objects_are_frozen(self):
        source = _source()
        self.assertIsInstance(source.product_ids, tuple)
        with self.assertRaises(AttributeError):
            source.product_ids.append("x")
        with self.assertRaises(FrozenInstanceError):
            source.title = "x"
        with self.assertRaises(FrozenInstanceError):
            source.identity.content_type = "x"
        with self.assertRaises(FrozenInstanceError):
            _state().chunk_count = 9

    def test_identity_rejects_empty_or_delimiter_components(self):
        for identity in (
            ("", "1", "en-US"),
            ("kb", "", "en-US"),
            ("kb", "1", ""),
            ("kb:wiki", "1", "en-US"),
            ("kb", "1:2", "en-US"),
            ("kb", "1", "en:US"),
        ):
            with self.subTest(identity=identity), self.assertRaises(InvalidDocumentState):
                ChunkIdentity(*identity)

    def test_chunk_id_rejects_invalid_positions(self):
        identity = ChunkIdentity("kb", "1", "en-US")
        for position in (-1, True, "0"):
            with self.subTest(position=position), self.assertRaises(InvalidDocumentState):
                chunk_id(identity, position)


class ChunkSourceStateContractTests(SimpleTestCase):
    def test_source_satisfies_the_state_hash_protocol(self):
        # ChunkSource must structurally satisfy fingerprints.ChunkStateSource, incl. access.
        source = _source(visibility="group_restricted", access_group_ids=[9, 7])
        digest = index_state_hash(
            [Chunk(text="x", position=0, heading_path="H", scope=())], source
        )
        self.assertEqual(len(digest), 64)

    def test_source_has_no_caller_supplied_hash(self):
        self.assertFalse(hasattr(_source(), "content_hash"))

    def test_unordered_collections_are_canonical_immutable_tuples(self):
        source = _source(
            product_ids=["9", "3"],
            topic_ids=["10", "2"],
            visibility="group_restricted",
            access_group_ids=[9, 7],
        )
        self.assertEqual(source.product_ids, ("3", "9"))
        self.assertEqual(source.topic_ids, ("10", "2"))
        self.assertEqual(source.access_group_ids, (7, 9))

    def test_access_metadata_must_be_consistent(self):
        invalid = (
            {"visibility": "public", "access_group_ids": [7]},
            {"visibility": "group_restricted", "access_group_ids": []},
            {"visibility": "unknown", "access_group_ids": []},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(InvalidDocumentState):
                _source(**overrides)

    def test_source_rejects_malformed_metadata(self):
        invalid = (
            {"family_id": ""},
            {"product_ids": ["3", "3"]},
            {"topic_ids": [3]},
            {"access_group_ids": [True], "visibility": "group_restricted"},
            {"updated": datetime(2026, 1, 1)},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(InvalidDocumentState):
                _source(**overrides)


class ExpectedDocumentStateTests(SimpleTestCase):
    def test_rejects_malformed_state(self):
        invalid = (
            {"content_hash": "not-a-digest"},
            {"index_state_hash": "g" * 64},
            {"chunking_generation": 0},
            {"chunking_generation": True},
            {"chunk_count": -1},
            {"indexed_revision_id": 0},
            {"indexed_revision_id": True},
            {"updated": datetime(2026, 1, 1)},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides), self.assertRaises(InvalidDocumentState):
                _state(**overrides)


class ScopeSerializationTests(SimpleTestCase):
    def test_comma_clause_remains_distinct_from_nested_clauses(self):
        comma = scope_envelope((frozenset({"win", "mac"}),))
        nested = scope_envelope((frozenset({"win"}), frozenset({"mac"})))
        self.assertEqual(comma, {"version": 1, "clauses": [["mac", "win"]]})
        self.assertEqual(nested, {"version": 1, "clauses": [["win"], ["mac"]]})
        self.assertNotEqual(comma, nested)


class ManifestSerializationTests(SimpleTestCase):
    def test_round_trips_including_zero_chunks(self):
        identity = ChunkIdentity("kb", "1", "en-US")
        state = _state(chunk_count=0)
        doc = manifest_doc(identity, state)
        self.assertEqual(doc.meta.id, "kb:1:en-US:manifest")
        self.assertEqual(parse_manifest(doc.to_dict()), state)

    def test_parses_elasticsearch_utc_string_timestamp(self):
        source = manifest_doc(ChunkIdentity("kb", "1", "en-US"), _state()).to_dict()
        source["updated"] = "2026-01-01T00:00:00.123456Z"
        parsed = parse_manifest(source)
        self.assertEqual(parsed.updated, datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=UTC))

    def test_manifest_marks_its_kind_and_omits_chunk_only_fields(self):
        source = manifest_doc(ChunkIdentity("kb", "1", "en-US"), _state()).to_dict()
        self.assertEqual(source["kind"], "manifest")
        self.assertEqual(
            (source["content_type"], source["object_id"], source["locale"]),
            ("kb", "1", "en-US"),
        )
        for chunk_only in (
            "content_text",
            "content_vector",
            "scope",
            "scope_clause_count",
            "visibility",
            "access_group_ids",
            "applies_to",
            "heading_path",
            "position",
            "family_id",
            "title",
            "summary",
            "keywords",
            "slug",
            "category",
            "product_ids",
            "topic_ids",
        ):
            self.assertNotIn(chunk_only, source)

    def test_parse_manifest_fails_closed_on_wrong_shape_or_kind(self):
        valid = manifest_doc(ChunkIdentity("kb", "1", "en-US"), _state()).to_dict()

        wrong_kind = dict(valid, kind="chunk")
        with self.assertRaises(InvalidDocumentState):
            parse_manifest(wrong_kind)

        missing_identity = dict(valid)
        del missing_identity["locale"]
        with self.assertRaises(InvalidDocumentState):
            parse_manifest(missing_identity)

        chunk_payload = dict(valid, content_text={"en-US": "body"})
        with self.assertRaises(InvalidDocumentState):
            parse_manifest(chunk_payload)

    def test_parse_manifest_fails_closed_on_invalid_state(self):
        valid = manifest_doc(ChunkIdentity("kb", "1", "en-US"), _state()).to_dict()
        invalid = (
            {"content_hash": "bad"},
            {"chunking_generation": -1},
            {"chunk_count": -1},
            {"indexed_revision_id": True},
            {"updated": "2026-01-01T00:00:00"},
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                source = dict(valid, **overrides)
                with self.assertRaises(InvalidDocumentState):
                    parse_manifest(source)


class ChunkPositionValidationTests(SimpleTestCase):
    def test_index_chunks_requires_contiguous_zero_based_positions(self):
        malformed = [
            [Chunk(text="a", position=-1, heading_path="H")],
            [Chunk(text="a", position=1, heading_path="H")],
            [
                Chunk(text="a", position=0, heading_path="H"),
                Chunk(text="b", position=0, heading_path="H"),
            ],
        ]
        for chunks in malformed:
            with self.subTest(positions=[chunk.position for chunk in chunks]):
                with self.assertRaises(InvalidDocumentState):
                    index_chunks(chunks, _source())


class ChunkDocumentMappingTests(ChunkIndexTestCase):
    def test_mapping_has_vector_text_and_metadata_fields(self):
        raw = es_client().indices.get_mapping(index=ChunkDocument.Index.read_alias)
        props = next(iter(raw.values()))["mappings"]["properties"]

        self.assertEqual(props["content_vector"]["type"], "dense_vector")
        self.assertEqual(props["content_vector"]["dims"], settings.RETRIEVAL_EMBEDDING_DIMENSIONS)
        self.assertEqual(props["content_vector"]["similarity"], "cosine")

        en = props["content_text"]["properties"]["en-US"]
        self.assertEqual(en["type"], "text")
        self.assertIn("analyzer", en)

        for locale_text in ("title", "summary", "keywords"):
            self.assertEqual(props[locale_text]["properties"]["en-US"]["type"], "text")
        self.assertEqual(props["slug"]["properties"]["en-US"]["type"], "keyword")

        for keyword_field in (
            "content_type",
            "locale",
            "category",
            "applies_to",
            "product_ids",
            "topic_ids",
            "kind",
            "visibility",
            "access_group_ids",
            "content_hash",
            "index_state_hash",
        ):
            self.assertEqual(props[keyword_field]["type"], "keyword")
        for integer_field in (
            "position",
            "scope_clause_count",
            "chunking_generation",
            "chunk_count",
        ):
            self.assertEqual(props[integer_field]["type"], "integer")
        self.assertEqual(props["indexed_revision_id"]["type"], "long")
        for date_field in ("updated", "indexed_on"):
            self.assertEqual(props[date_field]["type"], "date")
        # scope is stored losslessly in _source but not indexed.
        self.assertFalse(props["scope"].get("enabled", True))


class IndexChunksTests(ChunkIndexTestCase):
    def test_writes_a_doc_per_chunk_with_deterministic_ids_and_metadata(self):
        html = (
            "<h1>Install</h1>"
            "<p>Download and run the installer to get started.</p>"
            '<div class="for" data-for="win"><p>On Windows, double-click the setup file.</p></div>'
        )
        chunks = chunk_kb(html, title="Install Firefox")
        source = _source()

        index_chunks(chunks, source)

        self.assertEqual(ChunkDocument.search().count(), len(chunks))

        first = es_client().get(index=ChunkDocument.Index.read_alias, id="kb:1:en-US:0")["_source"]
        self.assertEqual(first["kind"], "chunk")
        self.assertEqual(first["content_text"]["en-US"], chunks[0].text)
        self.assertEqual(first["content_type"], "kb")
        self.assertEqual(first["object_id"], "1")
        self.assertEqual(first["family_id"], "1")
        self.assertEqual(first["position"], 0)
        self.assertEqual(first["content_hash"], content_hash(chunks))
        self.assertEqual(first["index_state_hash"], index_state_hash(chunks, source))
        self.assertEqual(first["chunking_generation"], CHUNKING_GENERATION)
        self.assertEqual(first["visibility"], "public")
        self.assertEqual(first["access_group_ids"], [])
        self.assertEqual(first["scope"], scope_envelope(chunks[0].scope))
        self.assertEqual(first["scope_clause_count"], 0)
        self.assertEqual(first["title"]["en-US"], "Install Firefox")
        # chunk docs carry no manifest-only fields
        self.assertNotIn("chunk_count", first)
        self.assertNotIn("indexed_revision_id", first)

        scoped = es_client().get(index=ChunkDocument.Index.read_alias, id="kb:1:en-US:1")[
            "_source"
        ]
        self.assertEqual(scoped["applies_to"], ["win"])
        self.assertEqual(scoped["scope"], scope_envelope(chunks[1].scope))
        self.assertEqual(scoped["scope"], {"version": 1, "clauses": [["win"]]})
        self.assertEqual(scoped["scope_clause_count"], 1)

    def test_restricted_source_writes_access_metadata(self):
        chunks = chunk_kb("<h1>H</h1><p>Body text here.</p>", title="T")
        source = _source(
            product_ids=["9", "3"],
            topic_ids=["4", "2"],
            visibility="group_restricted",
            access_group_ids=[9, 7],
        )
        index_chunks(chunks, source)
        stored = es_client().get(index=ChunkDocument.Index.read_alias, id="kb:1:en-US:0")[
            "_source"
        ]
        self.assertEqual(stored["visibility"], "group_restricted")
        # _source preserves integer group IDs; all unordered IDs use canonical order.
        self.assertEqual(stored["access_group_ids"], [7, 9])
        self.assertEqual(stored["product_ids"], ["3", "9"])
        self.assertEqual(stored["topic_ids"], ["2", "4"])


class DeleteChunksForTests(ChunkIndexTestCase):
    def test_deletes_only_the_targeted_documents_chunks(self):
        html = (
            "<h1>Sync</h1>"
            "<p>Turn on sync to share tabs across devices.</p>"
            "<h2>Devices</h2>"
            "<p>Manage your connected devices here.</p>"
        )
        chunks = chunk_kb(html, title="Sync")
        index_chunks(chunks, _source(object_id="1"))
        index_chunks(chunks, _source(object_id="2"))

        delete_chunks_for(content_type="kb", object_id="1", locale="en-US")

        self.assertEqual(ChunkDocument.search().filter("term", object_id="1").count(), 0)
        self.assertEqual(ChunkDocument.search().filter("term", object_id="2").count(), len(chunks))


class SearchInitCommandTests(ChunkIndexTestCase):
    def test_migrate_flags_create_index_and_point_both_aliases(self):
        # start from a clean slate so the fresh index can't collide with setUpClass's timestamp
        self._delete_indices()
        call_command("search_init", "--migrate-writes", "--migrate-reads")

        write_index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        read_index = ChunkDocument.alias_points_at(ChunkDocument.Index.read_alias)
        self.assertTrue(write_index)
        self.assertEqual(read_index, write_index)

    def test_no_flags_refreshes_existing_index_without_moving_aliases(self):
        before = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)
        call_command("search_init")
        self.assertEqual(ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias), before)
