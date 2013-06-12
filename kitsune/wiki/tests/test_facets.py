from nose.tools import eq_

from kitsune.products.tests import product
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.tests import TestCase
from kitsune.topics.tests import topic
from kitsune.wiki.facets import (
    topics_for, documents_for, _documents_for, _db_documents_for)
from kitsune.wiki.tests import revision


class TestFacetHelpersMixin(object):
    def facets_setUp(self):
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

        # An archived article shouldn't show up
        doc3 = revision(is_approved=True, save=True).document
        doc3.is_archived = True
        doc3.save()
        doc3.topics.add(self.general)
        doc3.topics.add(self.bookmarks)
        doc3.products.add(self.desktop)

        # A template article shouldn't show up either
        doc4 = revision(is_approved=True, save=True).document
        doc4.category = 60
        doc4.title = 'Template: Test'
        doc4.save()
        doc4.topics.add(self.general)
        doc4.topics.add(self.bookmarks)
        doc4.products.add(self.desktop)

        # An article without current revision should be "invisible"
        # to everything.
        doc5 = revision(is_approved=False, save=True).document
        doc5.topics.add(self.general)
        doc5.topics.add(self.bookmarks)
        doc5.topics.add(self.sync)
        doc5.products.add(self.desktop)
        doc5.products.add(self.mobile)


class TestFacetHelpers(TestCase, TestFacetHelpersMixin):
    def setUp(self):
        super(TestFacetHelpers, self).setUp()
        self.facets_setUp()

    def test_topics_for_products(self):
        """Verify topics_for() returns topics for passed products."""
        desktop_topics = topics_for(products=[self.desktop])
        eq_(len(desktop_topics), 3)

        mobile_topics = topics_for(products=[self.mobile])
        eq_(len(mobile_topics), 2)

        desktop_mobile_topics = topics_for(
            products=[self.desktop, self.mobile])
        eq_(len(desktop_mobile_topics), 2)


class TestFacetHelpersES(ElasticTestCase, TestFacetHelpersMixin):
    def setUp(self):
        super(TestFacetHelpersES, self).setUp()
        self.facets_setUp()
        self.refresh()

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
        # Test the default ES version
        self._test_documents_for(_documents_for)

        # Test the DB version
        self._test_documents_for(_db_documents_for)

    def test_documents_for_fallback(self):
        """Verify the fallback in documents_for."""
        general_bookmarks_documents, fallback = documents_for(
            locale='es', topics=[self.general, self.bookmarks])
        eq_(len(general_bookmarks_documents), 0)
        eq_(len(fallback), 1)
