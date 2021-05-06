from elasticsearch7.exceptions import NotFoundError

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.search.v2.documents import WikiDocument
from kitsune.search.v2.tests import Elastic7TestCase
from kitsune.wiki.tests import DocumentFactory, RevisionFactory


class WikiDocumentSignalsTests(Elastic7TestCase):
    def setUp(self):
        self.document = DocumentFactory()
        self.document_id = self.document.id

    def get_doc(self):
        return WikiDocument.get(self.document_id)

    def test_document_save(self):
        RevisionFactory(document=self.document, is_approved=True)
        self.document.title = "foobar"
        self.document.save()

        self.assertEqual(self.get_doc().title["en-US"], "foobar")

    def test_revision_save(self):
        RevisionFactory(document=self.document, is_approved=True, keywords="foobar")

        self.assertIn("foobar", self.get_doc().keywords["en-US"])

    def test_products_change(self):
        RevisionFactory(document=self.document, is_approved=True)
        product = ProductFactory()
        self.document.products.add(product)

        self.assertIn(product.id, self.get_doc().product_ids)

        self.document.products.remove(product)

        self.assertEqual(None, self.get_doc().product_ids)

    def test_topics_change(self):
        topic = TopicFactory()
        RevisionFactory(document=self.document, is_approved=True)
        self.document.topics.add(topic)

        self.assertIn(topic.id, self.get_doc().topic_ids)

        self.document.topics.remove(topic)

        self.assertEqual(None, self.get_doc().topic_ids)

    def test_document_delete(self):
        RevisionFactory(document=self.document, is_approved=True)
        self.document.delete()

        with self.assertRaises(NotFoundError):
            self.get_doc()

    def test_revision_delete(self):
        RevisionFactory(document=self.document, keywords="revision1", is_approved=True)
        revision2 = RevisionFactory(document=self.document, keywords="revision2", is_approved=True)
        self.assertEqual(self.get_doc().keywords["en-US"], "revision2")
        revision2.delete()

        self.assertNotIn("revision2", self.get_doc().keywords["en-US"])
        self.assertEqual(self.get_doc().keywords["en-US"], "revision1")

    def test_product_delete(self):
        RevisionFactory(document=self.document, is_approved=True)
        product = ProductFactory()
        self.document.products.add(product)
        product.delete()

        self.assertEqual(self.get_doc().product_ids, [])

    def test_topic_delete(self):
        RevisionFactory(document=self.document, is_approved=True)
        topic = TopicFactory()
        self.document.topics.add(topic)
        topic.delete()

        self.assertEqual(self.get_doc().topic_ids, [])

    def test_non_approved_revision_update(self):
        RevisionFactory(document=self.document, is_approved=False)

        with self.assertRaises(NotFoundError):
            self.get_doc()
