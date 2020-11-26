from kitsune.search.v2.tests import Elastic7TestCase
from kitsune.wiki.tests import DocumentFactory, RevisionFactory
from kitsune.products.tests import ProductFactory, TopicFactory
from elasticsearch7.exceptions import NotFoundError

from kitsune.search.v2.documents import WikiDocument


class WikiDocumentSignalsTests(Elastic7TestCase):
    def setUp(self):
        self.document = DocumentFactory()
        self.document_id = self.document.id

    @property
    def _doc(self):
        return WikiDocument.get(self.document_id)

    def test_document_save(self):
        self.document.title = "foobar"
        self.document.save()

        self.assertEqual(self._doc.title["en-US"], "foobar")

    def test_revision_save(self):
        revision = RevisionFactory(document=self.document, keywords="foobar")
        revision.is_approved = True
        revision.save()

        self.assertIn("foobar", self._doc.keywords["en-US"])

    def test_products_change(self):
        product = ProductFactory()
        self.document.products.add(product)

        self.assertIn(product.id, self._doc.product_ids)

        self.document.products.remove(product)

        self.assertEqual(None, self._doc.product_ids)

    def test_topics_change(self):
        topic = TopicFactory()
        self.document.topics.add(topic)

        self.assertIn(topic.id, self._doc.topic_ids)

        self.document.topics.remove(topic)

        self.assertEqual(None, self._doc.topic_ids)

    def test_document_delete(self):
        self.document.delete()

        with self.assertRaises(NotFoundError):
            self._doc

    def test_revision_delete(self):
        revision = RevisionFactory(document=self.document, keywords="foobar", is_approved=True)
        revision.delete()

        self.assertNotIn("foobar", self._doc.keywords["en-US"])

    def test_product_delete(self):
        product = ProductFactory()
        self.document.products.add(product)
        product.delete()

        self.assertEqual(self._doc.product_ids, [])

    def test_topic_delete(self):
        topic = TopicFactory()
        self.document.topics.add(topic)
        topic.delete()

        self.assertEqual(self._doc.topic_ids, [])
