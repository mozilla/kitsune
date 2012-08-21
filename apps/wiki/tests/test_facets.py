from nose.tools import eq_

from products.tests import product
from search.tests.test_es import ElasticTestCase
from topics.tests import topic
from wiki.facets import (products_for, topics_for, documents_for,
                         _db_products_for, _db_topics_for, _db_documents_for)
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

    def _test_products_for_topics(self, p_f):
        general_prods = p_f(topics=[self.general])
        eq_(len(general_prods), 1)
        eq_(general_prods[0].slug, self.desktop.slug)

        bookmarks_prods = p_f(topics=[self.bookmarks])
        eq_(len(bookmarks_prods), 2)

        bookmarks_sync_prods = p_f(
            topics=[self.bookmarks, self.sync])
        eq_(len(bookmarks_sync_prods), 2)

        bookmarks_general_prods = p_f(
            topics=[self.bookmarks, self.general])
        eq_(len(bookmarks_general_prods), 1)
        eq_(self.desktop.slug, bookmarks_general_prods[0].slug)

        sync_general_prods = p_f(topics=[self.sync, self.general])
        eq_(len(sync_general_prods), 0)

    def test_products_for_topics(self):
        """Verify products_for() returns products for passed topics."""
        self._test_products_for_topics(products_for)

    def test_db_products_for_topics(self):
        """Verify _db_products_for() returns products for passed topics."""
        self._test_products_for_topics(_db_products_for)

    def _test_topics_for_products(self, t_f):
        desktop_topics = t_f(products=[self.desktop])
        eq_(len(desktop_topics), 3)

        mobile_topics = t_f(products=[self.mobile])
        eq_(len(mobile_topics), 2)

        desktop_mobile_topics = t_f(
            products=[self.desktop, self.mobile])
        eq_(len(desktop_mobile_topics), 2)

    def test_topics_for_products(self):
        """Verify topics_for() returns topics for passed products."""
        self._test_topics_for_products(topics_for)

    def test_db_topics_for_products(self):
        """Verify _db_topics_for() returns topics for passed products."""
        self._test_topics_for_products(_db_topics_for)

    def _test_documents_for(self, d_f):
        general_documents = d_f(
            locale='en-US', topics=[self.general])
        eq_(len(general_documents), 1)

        bookmarks_documents = d_f(
            locale='en-US', topics=[self.bookmarks])
        eq_(len(bookmarks_documents), 2)

        sync_documents = d_f(locale='en-US', topics=[self.sync])
        eq_(len(sync_documents), 1)

        general_bookmarks_documents = d_f(
            locale='en-US', topics=[self.general, self.bookmarks])
        eq_(len(general_bookmarks_documents), 1)

        general_bookmarks_documents = d_f(
            locale='es', topics=[self.general, self.bookmarks])
        eq_(len(general_bookmarks_documents), 0)

        general_sync_documents = d_f(
            locale='en-US', topics=[self.general, self.sync])
        eq_(len(general_sync_documents), 0)

    def test_documents_for(self):
        """Verify documents_for() returns documents for passed topics."""
        self._test_documents_for(documents_for)

    def test_db_documents_for(self):
        """Verify _db_documents_for() returns dcouments for passed topics."""
        self._test_documents_for(_db_documents_for)
