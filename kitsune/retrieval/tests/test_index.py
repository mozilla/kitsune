from datetime import UTC, datetime

from django.conf import settings
from django.test import SimpleTestCase
from elasticsearch.dsl import Document as DSLDocument

from kitsune.retrieval.chunking import chunk_kb
from kitsune.retrieval.index import ChunkDocument, ChunkSource, index_chunks
from kitsune.retrieval.tests import ChunkIndexTestCase
from kitsune.search.base import AliasedIndexMixin
from kitsune.search.es_utils import es_client


class AliasedIndexMixinTests(SimpleTestCase):
    def test_declared_index_gets_prefixed_read_write_aliases(self):
        class Probe(AliasedIndexMixin, DSLDocument):
            class Index:
                pass

        base = f"{settings.ES_INDEX_PREFIX}_probe"
        self.assertEqual(Probe.Index.base_name, base)
        self.assertEqual(Probe.Index.read_alias, f"{base}_read")
        self.assertEqual(Probe.Index.write_alias, f"{base}_write")
        self.assertEqual(Probe.Index.name, Probe.Index.write_alias)

    def test_subclass_without_own_index_shares_parents_index(self):
        class Parent(AliasedIndexMixin, DSLDocument):
            class Index:
                pass

        class Child(Parent):
            pass

        self.assertEqual(Child.Index.base_name, Parent.Index.base_name)
        self.assertEqual(Child.Index.read_alias, Parent.Index.read_alias)


class ChunkDocumentMappingTests(ChunkIndexTestCase):
    def test_mapping_has_vector_text_and_metadata_fields(self):
        raw = es_client().indices.get_mapping(index=ChunkDocument.Index.read_alias)
        props = next(iter(raw.values()))["mappings"]["properties"]

        self.assertEqual(props["content_vector"]["type"], "dense_vector")
        self.assertEqual(props["content_vector"]["dims"], 768)
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
        ):
            self.assertEqual(props[keyword_field]["type"], "keyword")
        self.assertEqual(props["position"]["type"], "integer")
        self.assertEqual(props["updated"]["type"], "date")


class IndexChunksTests(ChunkIndexTestCase):
    def test_writes_a_doc_per_chunk_with_deterministic_ids_and_metadata(self):
        html = (
            "<h1>Install</h1>"
            "<p>Download and run the installer to get started.</p>"
            '<div class="for" data-for="win"><p>On Windows, double-click the setup file.</p></div>'
        )
        chunks = chunk_kb(html, title="Install Firefox")
        source = ChunkSource(
            content_type="kb",
            object_id="1",
            locale="en-US",
            family_id="1",
            title="Install Firefox",
            summary="How to install Firefox.",
            keywords="install setup",
            slug="install-firefox",
            category="10",
            product_ids=["3"],
            topic_ids=["10"],
            updated=datetime(2026, 1, 1, tzinfo=UTC),
            content_hash="abc123",
        )

        index_chunks(chunks, source)

        self.assertEqual(ChunkDocument.search().count(), len(chunks))

        first = es_client().get(index=ChunkDocument.Index.read_alias, id="kb:1:en-US:0")["_source"]
        self.assertEqual(first["content_text"]["en-US"], chunks[0].text)
        self.assertEqual(first["content_type"], "kb")
        self.assertEqual(first["object_id"], "1")
        self.assertEqual(first["locale"], "en-US")
        self.assertEqual(first["family_id"], "1")
        self.assertEqual(first["position"], 0)
        self.assertEqual(first["content_hash"], "abc123")
        self.assertEqual(first["title"]["en-US"], "Install Firefox")
        self.assertEqual(first["slug"]["en-US"], "install-firefox")
        self.assertEqual(first["product_ids"], ["3"])
        self.assertEqual(first["topic_ids"], ["10"])

        scoped = es_client().get(index=ChunkDocument.Index.read_alias, id="kb:1:en-US:1")[
            "_source"
        ]
        self.assertEqual(scoped["content_text"]["en-US"], chunks[1].text)
        self.assertEqual(scoped["applies_to"], ["win"])
