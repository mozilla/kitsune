from nose.tools import eq_

from products.tests import product
from search.tests.test_es import ElasticTestCase
from topics.tests import topic
from wiki.facets import products_for, topics_for, documents_for
from wiki.tests import revision


class TestFacetHelpers(ElasticTestCase):
    def setUp(self):
        super(TestFacetHelpers, self).setUp()

        # Create topics
        self.general = topic(slug='general', save=True)
        self.bookmarks = topic(slug='bookmarks', save=True)
        self.sync = topic(slug='sync', save=True)

        # Create products
        self.desktop = product(slug='firefox', save=True)
        self.mobile = product(slug='mobile', save=True)

        # Set up documents.
        doc1 = revision(is_approved=True, save=True).document
        doc1.topics.add(self.general)
        doc1.topics.add(self.bookmarks)
        doc1.products.add(self.desktop)

        doc2 = revision(is_approved=True, save=True).document
        doc2.topics.add(self.bookmarks)
        doc2.topics.add(self.sync)
        doc2.products.add(self.desktop)
        doc2.products.add(self.mobile)

        self.refresh()

    def test_products_for_topics(self):
        """Verify products_for() returns products for passed topics."""
        general_prods = products_for(topics=[self.general])
        eq_(1, len(general_prods))
        eq_(self.desktop.slug, general_prods[0].slug)

        bookmarks_prods = products_for(topics=[self.bookmarks])
        eq_(2, len(bookmarks_prods))

        bookmarks_sync_prods = products_for(
            topics=[self.bookmarks, self.sync])
        eq_(2, len(bookmarks_sync_prods))

        bookmarks_general_prods = products_for(
            topics=[self.bookmarks, self.general])
        eq_(1, len(bookmarks_general_prods))
        eq_(self.desktop.slug, bookmarks_general_prods[0].slug)

        sync_general_prods = products_for(topics=[self.sync, self.general])
        eq_(0, len(sync_general_prods))

    def test_topics_for_products(self):
        """Verify topics_for() returns products for passed products."""
        desktop_topics = topics_for(products=[self.desktop])
        eq_(3, len(desktop_topics))

        mobile_topics = topics_for(products=[self.mobile])
        eq_(2, len(mobile_topics))

        desktop_mobile_topics = topics_for(
            products=[self.desktop, self.mobile])
        eq_(2, len(desktop_mobile_topics))

    def test_documents_for_topics(self):
        general_documents = documents_for(
            locale='en-US', topics=[self.general])
        eq_(1, len(general_documents))

        bookmarks_documents = documents_for(
            locale='en-US', topics=[self.bookmarks])
        eq_(2, len(bookmarks_documents))

        sync_documents = documents_for(locale='en-US', topics=[self.sync])
        eq_(1, len(sync_documents))

        general_bookmarks_documents = documents_for(
            locale='en-US', topics=[self.general, self.bookmarks])
        eq_(1, len(general_bookmarks_documents))

        general_sync_documents = documents_for(
            locale='en-US', topics=[self.general, self.sync])
        eq_(0, len(general_sync_documents))
