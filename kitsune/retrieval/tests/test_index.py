from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase

from kitsune.retrieval.chunking import CHUNKING_GENERATION, Chunk, chunk_kb
from kitsune.retrieval.fingerprints import content_hash, index_state_hash, scope_envelope
from kitsune.retrieval.index import (
    VECTOR_DIMS,
    ChunkDocument,
    ChunkIdentity,
    ChunkSource,
    ExpectedDocumentState,
    IndexWriteError,
    InvalidDocumentState,
    chunk_id,
    commit_manifest,
    delete_chunks_for,
    delete_chunks_for_object,
    delete_orphan_chunks,
    manifest_doc,
    manifest_id,
    parse_manifest,
    read_indexed_document,
    repair_document_commit,
    replace_chunks,
    update_chunks_metadata_for,
    write_chunks,
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
    def test_write_chunks_requires_contiguous_zero_based_positions(self):
        source = _source()
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
                    write_chunks(
                        index=_physical_index_name(),
                        chunks=chunks,
                        vectors=[_vector(i) for i in range(len(chunks))],
                        source=source,
                        expected_state=_expected(chunks, source),
                    )


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


def _vector(seed):
    # Unit vector: distinct per seed and non-zero (cosine rejects zero-magnitude vectors).
    vector = [0.0] * VECTOR_DIMS
    vector[seed % VECTOR_DIMS] = 1.0
    return vector


def _expected(chunks, source, **overrides):
    fields = {
        "content_hash": content_hash(chunks),
        "index_state_hash": index_state_hash(chunks, source),
        "chunking_generation": CHUNKING_GENERATION,
        "chunk_count": len(chunks),
        "indexed_revision_id": 1,
        "updated": source.updated,
    }
    fields.update(overrides)
    return ExpectedDocumentState(**fields)


def _physical_index_name():
    return f"{ChunkDocument.Index.base_name}_20260101000000"


class WriteReadRoundTripTests(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)

    def _replace(self, chunks, source, **expected_kwargs):
        vectors = [_vector(i) for i in range(len(chunks))]
        replace_chunks(
            index=self.index,
            chunks=chunks,
            vectors=vectors,
            source=source,
            expected_state=_expected(chunks, source, **expected_kwargs),
        )
        return vectors

    def test_replace_then_read_round_trips_every_field(self):
        chunks = chunk_kb(
            "<h1>Install</h1><p>Download and run it.</p>"
            '<div class="for" data-for="win"><p>Windows steps.</p></div>',
            title="Install",
        )
        source = _source()
        vectors = self._replace(chunks, source)

        state = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(state.manifest, _expected(chunks, source))
        self.assertEqual([c["position"] for c in state.chunks], list(range(len(chunks))))
        first = state.chunks[0]
        self.assertEqual(first["kind"], "chunk")
        self.assertEqual(first["content_text"]["en-US"], chunks[0].text)
        self.assertEqual(first["content_vector"], vectors[0])
        self.assertEqual(first["content_type"], source.content_type)
        self.assertEqual(first["object_id"], source.object_id)
        self.assertEqual(first["family_id"], source.family_id)
        self.assertEqual(first["locale"], source.locale)
        self.assertEqual(first["position"], 0)
        self.assertEqual(first["heading_path"], chunks[0].heading_path)
        self.assertEqual(first["applies_to"], sorted(chunks[0].applies_to))
        self.assertEqual(first["scope"], scope_envelope(chunks[0].scope))
        self.assertEqual(first["scope_clause_count"], len(chunks[0].scope))
        self.assertEqual(first["visibility"], source.visibility)
        self.assertEqual(first["access_group_ids"], list(source.access_group_ids))
        self.assertEqual(first["content_hash"], content_hash(chunks))
        self.assertEqual(first["index_state_hash"], index_state_hash(chunks, source))
        self.assertEqual(first["chunking_generation"], CHUNKING_GENERATION)
        self.assertEqual(first["title"][source.locale], source.title)
        self.assertEqual(first["summary"][source.locale], source.summary)
        self.assertEqual(first["keywords"][source.locale], source.keywords)
        self.assertEqual(first["slug"][source.locale], source.slug)
        self.assertEqual(first["category"], source.category)
        self.assertEqual(first["product_ids"], list(source.product_ids))
        self.assertEqual(first["topic_ids"], list(source.topic_ids))
        self.assertIn("indexed_on", first)
        self.assertIn("updated", first)
        # chunk docs never carry manifest-only fields
        self.assertNotIn("chunk_count", first)
        self.assertNotIn("indexed_revision_id", first)

        scoped = state.chunks[1]
        self.assertEqual(scoped["content_vector"], vectors[1])
        self.assertEqual(scoped["applies_to"], ["win"])
        self.assertEqual(scoped["scope"], {"version": 1, "clauses": [["win"]]})
        self.assertEqual(scoped["scope_clause_count"], 1)

    def test_restricted_source_round_trips_canonical_access_metadata(self):
        source = _source(
            product_ids=["9", "3"],
            topic_ids=["4", "2"],
            visibility="group_restricted",
            access_group_ids=[9, 7],
        )
        chunks = [Chunk(text="body", position=0, heading_path="H")]
        self._replace(chunks, source)

        stored = read_indexed_document(index=self.index, identity=source.identity).chunks[0]
        self.assertEqual(stored["visibility"], "group_restricted")
        self.assertEqual(stored["access_group_ids"], [7, 9])
        self.assertEqual(stored["product_ids"], ["3", "9"])
        self.assertEqual(stored["topic_ids"], ["2", "4"])

    def test_reads_every_chunk_beyond_the_default_page(self):
        source = _source()
        chunks = [Chunk(text=f"body {i}", position=i, heading_path="H") for i in range(15)]
        self._replace(chunks, source)
        state = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual([c["position"] for c in state.chunks], list(range(15)))
        self.assertEqual(state.manifest.chunk_count, 15)

    def test_shrink_removes_orphan_chunks(self):
        source = _source()
        self._replace(
            [Chunk(text=f"b{i}", position=i, heading_path="H") for i in range(5)], source
        )
        self._replace(
            [Chunk(text=f"b{i}", position=i, heading_path="H") for i in range(3)], source
        )
        state = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual([c["position"] for c in state.chunks], [0, 1, 2])
        self.assertEqual(state.manifest.chunk_count, 3)

    def test_zero_chunks_commits_a_zero_manifest(self):
        source = _source()
        self._replace([Chunk(text="x", position=0, heading_path="H")], source)
        self._replace([], source)
        state = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(state.chunks, [])
        self.assertIsNotNone(state.manifest)  # "processed, empty" is not "missing"
        self.assertEqual(state.manifest.chunk_count, 0)

    def test_write_chunks_rejects_vector_or_expected_state_mismatches(self):
        source = _source()
        chunks = [Chunk(text=t, position=i, heading_path="H") for i, t in enumerate("ab")]
        mismatches = (
            ("vector count", [_vector(0)], {}),
            ("chunk count", [_vector(0), _vector(1)], {"chunk_count": 3}),
            ("content hash", [_vector(0), _vector(1)], {"content_hash": "f" * 64}),
            ("state hash", [_vector(0), _vector(1)], {"index_state_hash": "e" * 64}),
            (
                "updated timestamp",
                [_vector(0), _vector(1)],
                {"updated": datetime(2026, 1, 2, tzinfo=UTC)},
            ),
        )
        for reason, vectors, overrides in mismatches:
            with self.subTest(reason=reason), self.assertRaises(InvalidDocumentState):
                write_chunks(
                    index=self.index,
                    chunks=chunks,
                    vectors=vectors,
                    source=source,
                    expected_state=_expected(chunks, source, **overrides),
                )

    def test_manifest_identity_must_match_the_requested_document(self):
        requested = _source(object_id="1").identity
        wrong = _source(object_id="2").identity
        doc = manifest_doc(wrong, _expected([], _source(object_id="2")))
        es_client().index(
            index=self.index,
            id=manifest_id(requested),
            document=doc.to_dict(),
            refresh=True,
        )

        with self.assertRaises(InvalidDocumentState):
            read_indexed_document(index=self.index, identity=requested)


class ManifestCommitOrderingTests(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)

    def test_failed_replacement_keeps_the_previous_manifest_stale(self):
        source = _source()
        old_chunks = [Chunk(text="old", position=0, heading_path="H")]
        old_state = _expected(old_chunks, source, indexed_revision_id=1)
        replace_chunks(
            index=self.index,
            chunks=old_chunks,
            vectors=[_vector(0)],
            source=source,
            expected_state=old_state,
        )

        new_chunks = [Chunk(text="new", position=0, heading_path="H")]
        with (
            mock.patch(
                "kitsune.retrieval.index.bulk",
                return_value=(0, [{"index": {"status": 500}}]),
            ),
            self.assertRaises(IndexWriteError),
        ):
            replace_chunks(
                index=self.index,
                chunks=new_chunks,
                vectors=[_vector(1)],
                source=source,
                expected_state=_expected(new_chunks, source, indexed_revision_id=2),
            )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(stored.manifest, old_state)

    def test_failed_orphan_delete_does_not_advance_the_manifest(self):
        source = _source()
        old_chunks = [
            Chunk(text=f"old {position}", position=position, heading_path="H")
            for position in range(2)
        ]
        old_state = _expected(old_chunks, source, indexed_revision_id=1)
        replace_chunks(
            index=self.index,
            chunks=old_chunks,
            vectors=[_vector(0), _vector(1)],
            source=source,
            expected_state=old_state,
        )

        new_chunks = [Chunk(text="new", position=0, heading_path="H")]
        with (
            mock.patch(
                "kitsune.retrieval.index._verified_delete_by_query",
                side_effect=IndexWriteError("delete failed"),
            ),
            self.assertRaises(IndexWriteError),
        ):
            replace_chunks(
                index=self.index,
                chunks=new_chunks,
                vectors=[_vector(2)],
                source=source,
                expected_state=_expected(new_chunks, source, indexed_revision_id=2),
            )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(stored.manifest, old_state)


class MetadataUpdateTests(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)

    def _seed(self, chunks, source, **expected_kwargs):
        vectors = [_vector(i) for i in range(len(chunks))]
        replace_chunks(
            index=self.index,
            chunks=chunks,
            vectors=vectors,
            source=source,
            expected_state=_expected(chunks, source, **expected_kwargs),
        )
        return vectors

    def test_rewrites_metadata_while_preserving_text_and_vector(self):
        original = _source(
            visibility="group_restricted",
            access_group_ids=[9, 7],
        )
        chunks = [Chunk(text="body", position=0, heading_path="Old heading")]
        vectors = self._seed(chunks, original, indexed_revision_id=1)

        renamed = _source(
            family_id="7",
            title="Reinstall Firefox",
            summary="How to reinstall.",
            keywords="reinstall",
            slug="reinstall-firefox",
            category="20",
            product_ids=["9", "3"],
            topic_ids=["4"],
            visibility="group_restricted",
            access_group_ids=[9, 7],
        )
        rescoped = [
            Chunk(
                text="body",
                position=0,
                heading_path="New heading",
                scope=(frozenset({"win", "mac"}),),
            )
        ]
        state = _expected(rescoped, renamed, indexed_revision_id=2)
        update_chunks_metadata_for(
            index=self.index, chunks=rescoped, source=renamed, expected_state=state
        )

        stored = read_indexed_document(index=self.index, identity=renamed.identity)
        chunk = stored.chunks[0]
        self.assertEqual(chunk["content_text"]["en-US"], "body")
        self.assertEqual(chunk["content_vector"], vectors[0])
        self.assertEqual(chunk["heading_path"], "New heading")
        self.assertEqual(chunk["applies_to"], ["mac", "win"])
        self.assertEqual(chunk["scope"], scope_envelope(rescoped[0].scope))
        self.assertEqual(chunk["scope_clause_count"], 1)
        self.assertEqual(chunk["family_id"], "7")
        self.assertEqual(chunk["visibility"], "group_restricted")
        self.assertEqual(chunk["access_group_ids"], [7, 9])
        self.assertEqual(chunk["title"]["en-US"], "Reinstall Firefox")
        self.assertEqual(chunk["slug"]["en-US"], "reinstall-firefox")
        self.assertEqual(chunk["category"], "20")
        self.assertEqual(chunk["product_ids"], ["3", "9"])
        self.assertEqual(chunk["topic_ids"], ["4"])
        self.assertEqual(chunk["index_state_hash"], state.index_state_hash)
        self.assertEqual(chunk["chunking_generation"], state.chunking_generation)
        self.assertEqual(stored.manifest, state)

    def test_each_position_receives_its_own_scope_and_heading(self):
        source = _source()
        self._seed(
            [
                Chunk(text="a", position=0, heading_path="H0"),
                Chunk(text="b", position=1, heading_path="H1"),
            ],
            source,
        )

        rescoped = [
            Chunk(text="a", position=0, heading_path="Intro", scope=(frozenset({"win"}),)),
            Chunk(text="b", position=1, heading_path="Steps", scope=(frozenset({"mac"}),)),
        ]
        update_chunks_metadata_for(
            index=self.index,
            chunks=rescoped,
            source=source,
            expected_state=_expected(rescoped, source),
        )

        stored = read_indexed_document(index=self.index, identity=source.identity).chunks
        self.assertEqual([c["heading_path"] for c in stored], ["Intro", "Steps"])
        self.assertEqual([c["applies_to"] for c in stored], [["win"], ["mac"]])
        self.assertEqual([c["content_text"]["en-US"] for c in stored], ["a", "b"])

    def test_missing_position_fails_without_creating_a_chunk(self):
        source = _source()
        self._seed([Chunk(text="a", position=0, heading_path="H")], source, indexed_revision_id=1)

        grown = [
            Chunk(text="a", position=0, heading_path="H"),
            Chunk(text="b", position=1, heading_path="H"),
        ]
        with self.assertRaises(IndexWriteError):
            update_chunks_metadata_for(
                index=self.index,
                chunks=grown,
                source=source,
                expected_state=_expected(grown, source, indexed_revision_id=2),
            )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual([c["position"] for c in stored.chunks], [0])
        self.assertEqual(stored.manifest.indexed_revision_id, 1)

    def test_partial_update_leaves_the_manifest_stale(self):
        source = _source()
        chunks = [
            Chunk(text="a", position=0, heading_path="H"),
            Chunk(text="b", position=1, heading_path="H"),
        ]
        self._seed(chunks, source, indexed_revision_id=1)

        with (
            mock.patch(
                "kitsune.retrieval.index.bulk",
                return_value=(1, [{"update": {"status": 500}}]),
            ),
            self.assertRaises(IndexWriteError),
        ):
            update_chunks_metadata_for(
                index=self.index,
                chunks=chunks,
                source=source,
                expected_state=_expected(chunks, source, indexed_revision_id=2),
            )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(stored.manifest.indexed_revision_id, 1)

    def test_failed_orphan_delete_does_not_advance_the_manifest(self):
        source = _source()
        chunks = [Chunk(text=f"b{i}", position=i, heading_path="H") for i in range(2)]
        self._seed(chunks, source, indexed_revision_id=1)

        kept = chunks[:1]
        with (
            mock.patch(
                "kitsune.retrieval.index._verified_delete_by_query",
                side_effect=IndexWriteError("delete failed"),
            ),
            self.assertRaises(IndexWriteError),
        ):
            update_chunks_metadata_for(
                index=self.index,
                chunks=kept,
                source=source,
                expected_state=_expected(kept, source, indexed_revision_id=2),
            )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(stored.manifest.indexed_revision_id, 1)

    def test_shrinking_update_removes_orphans_and_commits(self):
        source = _source()
        self._seed([Chunk(text=f"b{i}", position=i, heading_path="H") for i in range(4)], source)

        kept = [Chunk(text=f"b{i}", position=i, heading_path="Kept") for i in range(2)]
        update_chunks_metadata_for(
            index=self.index, chunks=kept, source=source, expected_state=_expected(kept, source)
        )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual([c["position"] for c in stored.chunks], [0, 1])
        self.assertEqual(stored.manifest.chunk_count, 2)

    def test_zero_chunks_removes_leftovers_and_commits_zero(self):
        source = _source()
        self._seed([Chunk(text="a", position=0, heading_path="H")], source)

        update_chunks_metadata_for(
            index=self.index, chunks=[], source=source, expected_state=_expected([], source)
        )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(stored.chunks, [])
        self.assertEqual(stored.manifest.chunk_count, 0)

    def test_rejects_expected_state_mismatches_and_bad_positions(self):
        source = _source()
        chunks = [Chunk(text=t, position=i, heading_path="H") for i, t in enumerate("ab")]
        for reason, overrides in (
            ("chunk count", {"chunk_count": 3}),
            ("content hash", {"content_hash": "f" * 64}),
            ("state hash", {"index_state_hash": "e" * 64}),
            ("updated timestamp", {"updated": datetime(2026, 1, 2, tzinfo=UTC)}),
        ):
            with self.subTest(reason=reason), self.assertRaises(InvalidDocumentState):
                update_chunks_metadata_for(
                    index=self.index,
                    chunks=chunks,
                    source=source,
                    expected_state=_expected(chunks, source, **overrides),
                )

        noncontiguous = [Chunk(text="a", position=1, heading_path="H")]
        with self.assertRaises(InvalidDocumentState):
            update_chunks_metadata_for(
                index=self.index,
                chunks=noncontiguous,
                source=source,
                expected_state=_expected(noncontiguous, source),
            )

    def test_emptied_metadata_collections_are_cleared_in_the_index(self):
        source = _source(product_ids=["3", "9"], topic_ids=["10"], summary="A summary.")
        chunks = [Chunk(text="a", position=0, heading_path="H")]
        self._seed(chunks, source)

        cleared = _source(product_ids=[], topic_ids=[], summary="")
        update_chunks_metadata_for(
            index=self.index,
            chunks=chunks,
            source=cleared,
            expected_state=_expected(chunks, cleared),
        )

        stored = read_indexed_document(index=self.index, identity=cleared.identity).chunks[0]
        self.assertEqual(stored["product_ids"], [])
        self.assertEqual(stored["topic_ids"], [])
        self.assertEqual(stored["summary"]["en-US"], "")

    def test_makes_no_embedding_calls(self):
        source = _source()
        chunks = [Chunk(text="a", position=0, heading_path="H")]
        self._seed(chunks, source)

        with mock.patch(
            "kitsune.retrieval.embeddings.get_embeddings",
            side_effect=AssertionError("a metadata update must never embed"),
        ):
            update_chunks_metadata_for(
                index=self.index,
                chunks=chunks,
                source=source,
                expected_state=_expected(chunks, source),
            )


class CommitRepairTests(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)

    def _seed(self, count, source, **expected_kwargs):
        chunks = [Chunk(text=f"b{i}", position=i, heading_path="H") for i in range(count)]
        replace_chunks(
            index=self.index,
            chunks=chunks,
            vectors=[_vector(i) for i in range(count)],
            source=source,
            expected_state=_expected(chunks, source, **expected_kwargs),
        )
        return chunks

    def test_deletes_known_orphans_and_commits_the_manifest(self):
        source = _source()
        chunks = self._seed(5, source, indexed_revision_id=1)
        expected = _expected(chunks[:3], source, indexed_revision_id=2)

        repair_document_commit(
            index=self.index,
            identity=source.identity,
            expected_state=expected,
            orphan_positions={3, 4},
        )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual([c["position"] for c in stored.chunks], [0, 1, 2])
        self.assertEqual(stored.manifest, expected)

    def test_no_orphans_commits_without_a_delete(self):
        source = _source()
        chunks = self._seed(2, source, indexed_revision_id=1)
        expected = _expected(chunks, source, indexed_revision_id=2)

        with mock.patch("kitsune.retrieval.index._verified_delete_by_query") as delete:
            repair_document_commit(
                index=self.index,
                identity=source.identity,
                expected_state=expected,
                orphan_positions=set(),
            )
        delete.assert_not_called()

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(stored.manifest, expected)

    def test_refuses_to_delete_an_expected_position(self):
        source = _source()
        chunks = self._seed(3, source, indexed_revision_id=1)
        expected = _expected(chunks, source, indexed_revision_id=2)

        for orphans in ({0}, {2}, {1, 3}):
            with self.subTest(orphans=orphans), self.assertRaises(InvalidDocumentState):
                repair_document_commit(
                    index=self.index,
                    identity=source.identity,
                    expected_state=expected,
                    orphan_positions=orphans,
                )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual([c["position"] for c in stored.chunks], [0, 1, 2])
        self.assertEqual(stored.manifest.indexed_revision_id, 1)

    def test_rejects_malformed_orphan_positions(self):
        source = _source()
        chunks = self._seed(1, source)
        expected = _expected(chunks, source)

        for orphans in ({-1}, {True}, {"3"}, [1.5], "12", 3, None):
            with self.subTest(orphans=orphans), self.assertRaises(InvalidDocumentState):
                repair_document_commit(
                    index=self.index,
                    identity=source.identity,
                    expected_state=expected,
                    orphan_positions=orphans,
                )

    def test_failed_orphan_delete_does_not_commit(self):
        source = _source()
        chunks = self._seed(3, source, indexed_revision_id=1)
        expected = _expected(chunks[:2], source, indexed_revision_id=2)

        with (
            mock.patch(
                "kitsune.retrieval.index._verified_delete_by_query",
                side_effect=IndexWriteError("delete failed"),
            ),
            self.assertRaises(IndexWriteError),
        ):
            repair_document_commit(
                index=self.index,
                identity=source.identity,
                expected_state=expected,
                orphan_positions={2},
            )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual(stored.manifest.indexed_revision_id, 1)

    def test_repairs_only_the_requested_document(self):
        target, other = _source(object_id="1"), _source(object_id="2")
        target_chunks = self._seed(3, target)
        self._seed(3, other)

        repair_document_commit(
            index=self.index,
            identity=target.identity,
            expected_state=_expected(target_chunks[:1], target),
            orphan_positions={1, 2},
        )

        kept = read_indexed_document(index=self.index, identity=other.identity)
        self.assertEqual([c["position"] for c in kept.chunks], [0, 1, 2])
        self.assertEqual(kept.manifest.chunk_count, 3)

    def test_makes_no_embedding_calls(self):
        source = _source()
        chunks = self._seed(2, source)

        with mock.patch(
            "kitsune.retrieval.embeddings.get_embeddings",
            side_effect=AssertionError("a commit repair must never embed"),
        ):
            repair_document_commit(
                index=self.index,
                identity=source.identity,
                expected_state=_expected(chunks[:1], source),
                orphan_positions={1},
            )

        stored = read_indexed_document(index=self.index, identity=source.identity)
        self.assertEqual([c["position"] for c in stored.chunks], [0])


class DeleteTests(ChunkIndexTestCase):
    def setUp(self):
        super().setUp()
        self.index = ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias)

    def _seed(self, source):
        chunks = [Chunk(text="x", position=0, heading_path="H")]
        replace_chunks(
            index=self.index,
            chunks=chunks,
            vectors=[_vector(0)],
            source=source,
            expected_state=_expected(chunks, source),
        )

    def test_delete_chunks_for_removes_chunks_and_manifest(self):
        target, other = _source(object_id="1"), _source(object_id="2")
        self._seed(target)
        self._seed(other)

        delete_chunks_for(index=self.index, identity=target.identity)

        gone = read_indexed_document(index=self.index, identity=target.identity)
        self.assertEqual(gone.chunks, [])
        self.assertIsNone(gone.manifest)
        kept = read_indexed_document(index=self.index, identity=other.identity)
        self.assertEqual(len(kept.chunks), 1)
        self.assertIsNotNone(kept.manifest)

    def test_delete_chunks_for_object_removes_all_locales_of_one_object(self):
        english, german = (
            _source(object_id="1", locale="en-US"),
            _source(object_id="1", locale="de"),
        )
        other = _source(object_id="2", locale="en-US")
        other_type = _source(content_type="question", object_id="1", locale="en-US")
        for source in (english, german, other, other_type):
            self._seed(source)

        delete_chunks_for_object(index=self.index, content_type="kb", object_id="1")

        deleted_english = read_indexed_document(index=self.index, identity=english.identity)
        deleted_german = read_indexed_document(index=self.index, identity=german.identity)
        kept_other = read_indexed_document(index=self.index, identity=other.identity)
        kept_other_type = read_indexed_document(index=self.index, identity=other_type.identity)
        for deleted in (deleted_english, deleted_german):
            self.assertEqual(deleted.chunks, [])
            self.assertIsNone(deleted.manifest)
        for kept in (kept_other, kept_other_type):
            self.assertEqual(len(kept.chunks), 1)
            self.assertIsNotNone(kept.manifest)

    def test_delete_chunks_for_object_rejects_malformed_identity(self):
        for content_type, object_id in (("", "1"), ("kb", ""), ("kb:wiki", "1"), ("kb", "1:2")):
            with (
                self.subTest(content_type=content_type, object_id=object_id),
                self.assertRaises(InvalidDocumentState),
            ):
                delete_chunks_for_object(
                    index=self.index, content_type=content_type, object_id=object_id
                )

    def test_delete_fails_closed_when_delete_by_query_is_not_fully_successful(self):
        responses = (
            {
                "timed_out": True,
                "failures": [],
                "version_conflicts": 0,
                "total": 1,
                "deleted": 1,
            },
            {
                "timed_out": False,
                "failures": [{"shard": 1}],
                "version_conflicts": 0,
                "total": 1,
                "deleted": 0,
            },
            {
                "timed_out": False,
                "failures": [],
                "version_conflicts": 1,
                "total": 1,
                "deleted": 0,
            },
            {},
        )
        for response in responses:
            client = mock.Mock()
            client.delete_by_query.return_value = response
            with (
                self.subTest(response=response),
                mock.patch("kitsune.retrieval.index.es_client", return_value=client),
                self.assertRaises(IndexWriteError),
            ):
                delete_chunks_for(index=self.index, identity=_source().identity)


class ConcreteIndexGuardTests(SimpleTestCase):
    def test_physical_primitives_reject_aliases_and_non_generation_names(self):
        source = _source()
        chunks = [Chunk(text="x", position=0, heading_path="H")]
        state = _expected(chunks, source)
        invalid_indexes = (
            ChunkDocument.Index.write_alias,
            ChunkDocument.Index.read_alias,
            "some-other-alias",
            "",
        )

        for index in invalid_indexes:
            with self.subTest(index=index):
                with self.assertRaises(InvalidDocumentState):
                    write_chunks(
                        index=index,
                        chunks=chunks,
                        vectors=[_vector(0)],
                        source=source,
                        expected_state=state,
                    )
                with self.assertRaises(InvalidDocumentState):
                    replace_chunks(
                        index=index,
                        chunks=chunks,
                        vectors=[_vector(0)],
                        source=source,
                        expected_state=state,
                    )
                with self.assertRaises(InvalidDocumentState):
                    commit_manifest(index=index, identity=source.identity, expected_state=state)
                with self.assertRaises(InvalidDocumentState):
                    delete_orphan_chunks(
                        index=index, identity=source.identity, expected_positions={0}
                    )
                with self.assertRaises(InvalidDocumentState):
                    read_indexed_document(index=index, identity=source.identity)
                with self.assertRaises(InvalidDocumentState):
                    delete_chunks_for(index=index, identity=source.identity)
                with self.assertRaises(InvalidDocumentState):
                    delete_chunks_for_object(index=index, content_type="kb", object_id="1")
                with self.assertRaises(InvalidDocumentState):
                    update_chunks_metadata_for(
                        index=index, chunks=chunks, source=source, expected_state=state
                    )
                with self.assertRaises(InvalidDocumentState):
                    repair_document_commit(
                        index=index,
                        identity=source.identity,
                        expected_state=state,
                        orphan_positions={1},
                    )
