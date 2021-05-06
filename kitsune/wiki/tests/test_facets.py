from nose.tools import eq_

from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.facets import topics_for, documents_for, _documents_for
from kitsune.wiki.tests import (
    DocumentFactory,
    TemplateDocumentFactory,
    RevisionFactory,
    ApprovedRevisionFactory,
)


class TestFacetHelpers(TestCase):
    def setUp(self):
        super(TestFacetHelpers, self).setUp()
        # Create products
        self.desktop = ProductFactory(slug="firefox")
        self.mobile = ProductFactory(slug="mobile")

        # Create topics
        self.general_d = TopicFactory(product=self.desktop, slug="general")
        self.bookmarks_d = TopicFactory(product=self.desktop, slug="bookmarks")
        self.sync_d = TopicFactory(product=self.desktop, slug="sync")
        self.general_m = TopicFactory(product=self.mobile, slug="general")
        self.bookmarks_m = TopicFactory(product=self.mobile, slug="bookmarks")
        self.sync_m = TopicFactory(product=self.mobile, slug="sync")

        # Set up documents.
        doc1 = DocumentFactory(products=[self.desktop], topics=[self.general_d, self.bookmarks_d])
        doc1_revision = ApprovedRevisionFactory(document=doc1, is_ready_for_localization=True)

        doc1_localized = DocumentFactory(locale="de", products=[], topics=[], parent=doc1)
        ApprovedRevisionFactory(document=doc1_localized, based_on=doc1_revision)

        doc2 = DocumentFactory(
            products=[self.desktop, self.mobile],
            topics=[self.bookmarks_d, self.bookmarks_m, self.sync_d, self.sync_m],
        )
        ApprovedRevisionFactory(document=doc2)

        # An archived article shouldn't show up
        doc3 = DocumentFactory(
            is_archived=True, products=[self.desktop], topics=[self.general_d, self.bookmarks_d]
        )
        ApprovedRevisionFactory(document=doc3)

        # A template article shouldn't show up either
        doc4 = TemplateDocumentFactory(
            products=[self.desktop], topics=[self.general_d, self.bookmarks_d]
        )
        ApprovedRevisionFactory(document=doc4)

        # An article without current revision should be "invisible"
        # to everything.
        doc5 = DocumentFactory(
            products=[self.desktop, self.mobile],
            topics=[
                self.general_d,
                self.bookmarks_d,
                self.sync_d,
                self.general_m,
                self.bookmarks_m,
                self.sync_m,
            ],
        )
        RevisionFactory(is_approved=False, document=doc5)

    def test_topics_for_products(self):
        """Verify topics_for() returns topics for passed products."""
        desktop_topics = topics_for(product=self.desktop)
        eq_(len(desktop_topics), 3)

        mobile_topics = topics_for(product=self.mobile)
        eq_(len(mobile_topics), 2)

    def test_documents_for(self):
        """Verify documents_for() returns documents for passed topics."""
        general_documents = _documents_for(locale="en-US", topics=[self.general_d])
        eq_(len(general_documents), 1)

        bookmarks_documents = _documents_for(locale="en-US", topics=[self.bookmarks_d])
        eq_(len(bookmarks_documents), 2)

        sync_documents = _documents_for(locale="en-US", topics=[self.sync_d])
        eq_(len(sync_documents), 1)

        general_bookmarks_documents = _documents_for(
            locale="en-US", topics=[self.general_d, self.bookmarks_d]
        )
        eq_(len(general_bookmarks_documents), 1)

        general_bookmarks_documents_localized = _documents_for(
            locale="de", topics=[self.general_d, self.bookmarks_d]
        )
        eq_(len(general_bookmarks_documents_localized), 1)

        general_sync_documents = _documents_for(
            locale="en-US", topics=[self.general_d, self.sync_d]
        )
        eq_(len(general_sync_documents), 0)

    def test_documents_for_fallback(self):
        """Verify the fallback in documents_for."""
        general_bookmarks_documents, fallback = documents_for(
            locale="es", topics=[self.general_d, self.bookmarks_d]
        )
        eq_(len(general_bookmarks_documents), 0)
        eq_(len(fallback), 1)
