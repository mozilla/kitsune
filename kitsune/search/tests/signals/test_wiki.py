from elasticsearch import NotFoundError

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.search.documents import WikiDocument
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory
from kitsune.wiki.config import (
    ADMINISTRATION_CATEGORY,
    CANNED_RESPONSES_CATEGORY,
    REDIRECT_HTML,
    TROUBLESHOOTING_CATEGORY,
)
from kitsune.wiki.models import Document
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RevisionFactory,
    TemplateDocumentFactory,
)


class WikiDocumentSignalsTests(ElasticTestCase):
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

        self.assertEqual([], self.get_doc().product_ids)

    def test_topics_change(self):
        topic = TopicFactory()
        RevisionFactory(document=self.document, is_approved=True)
        self.document.topics.add(topic)

        self.assertIn(topic.id, self.get_doc().topic_ids)

        self.document.topics.remove(topic)

        self.assertEqual([], self.get_doc().topic_ids)

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


class WikiDocumentPrepareDiscardTests(TestCase):
    """`prepare` discards exactly the public-indexing-disallowed set (Task 3 refactor).

    The discard decision now delegates to the shared `is_public_indexing_allowed` rule.
    A revision-less translation must NOT be discarded here: discarding it under the
    parent's ES id could unindex the whole merged-locale family.
    """

    def assert_discarded(self, doc, expected):
        prepared = Document.objects.get(pk=doc.pk)
        WikiDocument.prepare(prepared)
        self.assertEqual(hasattr(prepared, "es_discard_doc"), expected)

    def test_normal_document_not_discarded(self):
        doc = DocumentFactory()
        ApprovedRevisionFactory(document=doc)
        self.assert_discarded(doc, False)

    def test_restricted_discarded(self):
        doc = DocumentFactory(restrict_to_groups=[GroupFactory()])
        ApprovedRevisionFactory(document=doc)
        self.assert_discarded(doc, True)

    def test_archived_discarded(self):
        self.assert_discarded(DocumentFactory(is_archived=True), True)

    def test_template_discarded(self):
        self.assert_discarded(TemplateDocumentFactory(), True)

    def test_stale_template_translation_discarded_after_parent_category_change(self):
        parent = TemplateDocumentFactory()
        translation = TemplateDocumentFactory(parent=parent, locale="de")
        ApprovedRevisionFactory(document=translation)

        parent.title = "Former template"
        parent.category = TROUBLESHOOTING_CATEGORY
        parent.save()
        translation.refresh_from_db()

        self.assertTrue(translation.is_template)
        self.assertEqual(translation.category, TROUBLESHOOTING_CATEGORY)
        self.assert_discarded(translation, True)

    def test_translation_inheriting_archived_parent_discarded(self):
        parent = DocumentFactory(is_archived=True)
        translation = DocumentFactory(parent=parent, locale="de")
        self.assertTrue(translation.is_archived)
        self.assert_discarded(translation, True)

    def test_canned_response_discarded(self):
        self.assert_discarded(DocumentFactory(category=CANNED_RESPONSES_CATEGORY), True)

    def test_administration_discarded(self):
        self.assert_discarded(DocumentFactory(category=ADMINISTRATION_CATEGORY), True)

    def test_redirect_discarded(self):
        doc = DocumentFactory()
        Document.objects.filter(pk=doc.pk).update(html=REDIRECT_HTML + '<a href="/x">x</a></p>')
        self.assert_discarded(doc, True)

    def test_revision_less_translation_not_discarded(self):
        parent = DocumentFactory()
        ApprovedRevisionFactory(document=parent)
        translation = DocumentFactory(parent=Document.objects.get(pk=parent.pk), locale="de")
        # No approved revision → revision-less; prepare must not discard it.
        self.assert_discarded(translation, False)
