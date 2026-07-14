from django.conf import settings
from django.test import SimpleTestCase
from elasticsearch.dsl import Document as DSLDocument

from kitsune.retrieval.index import ChunkDocument
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
