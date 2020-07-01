from django.conf import settings
from django.core.cache import cache
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.products.models import HOT_TOPIC_SLUG
from kitsune.products.tests import ProductFactory
from kitsune.products.tests import TopicFactory
from kitsune.questions.models import QuestionLocale
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import ApprovedRevisionFactory
from kitsune.wiki.tests import DocumentFactory
from kitsune.wiki.tests import HelpfulVoteFactory


class ProductViewsTestCase(ElasticTestCase):
    def test_products(self):
        """Verify that /products page renders products."""
        # Create some products.
        for i in range(3):
            p = ProductFactory(visible=True)
            locale = QuestionLocale.objects.get(locale=settings.LANGUAGE_CODE)
            p.questions_locales.add(locale)

        # GET the products page and verify the content.
        r = self.client.get(reverse("products"), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc("#products-and-services li")))

    def test_product_landing(self):
        """Verify that /products/<slug> page renders topics."""
        # Create a product.
        p = ProductFactory()
        locale = QuestionLocale.objects.get(locale=settings.LANGUAGE_CODE)
        p.questions_locales.add(locale)

        # Create some topics.
        TopicFactory(slug=HOT_TOPIC_SLUG, product=p, visible=True)
        topics = TopicFactory.create_batch(11, product=p, visible=True)

        # Create a document and assign the product and 10 topics.
        d = DocumentFactory(products=[p], topics=topics[:10])
        ApprovedRevisionFactory(document=d)

        self.refresh()

        # GET the product landing page and verify the content.
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(11, len(doc("#help-topics li")))
        eq_(p.slug, doc("#support-search input[name=product]").attr["value"])

    def test_firefox_product_landing(self):
        """Verify that there are no firefox button at header in the firefox landing page"""
        p = ProductFactory(slug="firefox")
        url = reverse("products.product", args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(False, doc(".firefox-download-button").length)

    def test_document_listing(self):
        """Verify /products/<product slug>/<topic slug> renders articles."""
        # Create a topic and product.
        p = ProductFactory()
        t1 = TopicFactory(product=p)

        # Create 3 documents with the topic and product and one without.
        ApprovedRevisionFactory.create_batch(3, document__products=[p], document__topics=[t1])
        ApprovedRevisionFactory()

        self.refresh()

        # GET the page and verify the content.
        url = reverse("products.documents", args=[p.slug, t1.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc("#document-list > ul > li")))
        eq_(p.slug, doc("#support-search input[name=product]").attr["value"])

    def test_document_listing_order(self):
        """Verify documents are sorted by display_order and number of helpful votes."""
        # Create topic, product and documents.
        p = ProductFactory()
        t = TopicFactory(product=p)
        docs = []
        # FIXME: Can't we do this with create_batch and build the document
        # in the approvedrevisionfactory
        for i in range(3):
            doc = DocumentFactory(products=[p], topics=[t])
            ApprovedRevisionFactory(document=doc)
            docs.append(doc)

        # Add a lower display order to the second document. It should be first now.
        docs[1].display_order = 0
        docs[1].save()
        self.refresh()
        url = reverse("products.documents", args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(doc("#document-list > ul > li:first-child > a").text(), docs[1].title)

        # Add a helpful vote to the third document. It should be second now.
        rev = docs[2].current_revision
        HelpfulVoteFactory(revision=rev, helpful=True)
        docs[2].save()  # Votes don't trigger a reindex.
        self.refresh()
        cache.clear()  # documents_for() is cached
        url = reverse("products.documents", args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(doc("#document-list > ul > li:nth-child(2) > a").text(), docs[2].title)

        # Add 2 helpful votes the first document. It should be second now.
        rev = docs[0].current_revision
        HelpfulVoteFactory(revision=rev, helpful=True)
        HelpfulVoteFactory(revision=rev, helpful=True)
        docs[0].save()  # Votes don't trigger a reindex.
        self.refresh()
        cache.clear()  # documents_for() is cached
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(doc("#document-list > ul > li:nth-child(2) > a").text(), docs[0].title)

    def test_subtopics(self):
        """Verifies subtopics appear on document listing page."""
        # Create a topic and product.
        p = ProductFactory()
        t = TopicFactory(product=p, visible=True)

        # Create a documents with the topic and product
        doc = DocumentFactory(products=[p], topics=[t])
        ApprovedRevisionFactory(document=doc)

        self.refresh()

        # GET the page and verify no subtopics yet.
        url = reverse("products.documents", args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        pqdoc = pq(r.content)
        eq_(0, len(pqdoc("li.subtopic")))

        # Create a subtopic, it still shouldn't show up because no
        # articles are assigned.
        subtopic = TopicFactory(parent=t, product=p, visible=True)
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        pqdoc = pq(r.content)
        eq_(0, len(pqdoc("li.subtopic")))

        # Add a document to the subtopic, now it should appear.
        doc.topics.add(subtopic)
        self.refresh()

        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        pqdoc = pq(r.content)
        eq_(1, len(pqdoc("li.subtopic")))
