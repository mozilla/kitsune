from django.core.cache import cache

from nose.tools import eq_
from pyquery import PyQuery as pq
from waffle.models import Flag

from kitsune.products.tests import product, topic as new_topic
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.topics.models import HOT_TOPIC_SLUG
from kitsune.topics.tests import topic
from kitsune.wiki.tests import revision, helpful_vote


# TODO: Remove this class when removing old topics
class ProductViewsTestCase(ElasticTestCase):
    def test_products(self):
        """Verify that /products page renders products."""
        # Create some products.
        for i in range(3):
            product(save=True)

        # GET the products page and verify the content.
        r = self.client.get(reverse('products'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(4, len(doc('#products-and-services li')))

    def test_product_landing(self):
        """Verify that /products/<slug> page renders topics."""
        # Create a product.
        p = product(save=True)

        # Create some topics.
        topic(slug=HOT_TOPIC_SLUG, save=True)
        topics = []
        for i in range(11):
            topics.append(topic(save=True))

        # Create a document and assign the product and 10 topics.
        doc = revision(is_approved=True, save=True).document
        doc.products.add(p)
        for i in range(10):
            doc.topics.add(topics[i])

        self.refresh()

        # GET the product landing page and verify the content.
        url = reverse('products.product', args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(11, len(doc('#help-topics li')))
        eq_(p.slug, doc('#support-search input[name=product]').attr['value'])

    def test_document_listing(self):
        """Verify /products/<product slug>/<topic slug> renders articles."""
        # Create a topic and product.
        t1 = topic(save=True)
        p = product(save=True)

        # Create 3 documents with the topic and product and one without.
        for i in range(3):
            doc = revision(is_approved=True, save=True).document
            doc.topics.add(t1)
            doc.products.add(p)

        doc = revision(is_approved=True, save=True).document

        self.refresh()

        # GET the page and verify the content.
        url = reverse('products.documents', args=[p.slug, t1.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc('#document-list > ul > li')))
        eq_(p.slug, doc('#support-search input[name=product]').attr['value'])

    def test_document_listing_order(self):
        """Verify documents are listed in order of helpful votes."""
        # Create topic, product and documents.
        t = topic(save=True)
        p = product(save=True)
        docs = []
        for i in range(3):
            doc = revision(is_approved=True, save=True).document
            doc.topics.add(t)
            doc.products.add(p)
            docs.append(doc)

        # Add a helpful vote to the second document. It should be first now.
        rev = docs[1].current_revision
        helpful_vote(revision=rev, helpful=True, save=True)
        docs[1].save()  # Votes don't trigger a reindex.
        self.refresh()
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(doc('#document-list > ul > li:first').text(), docs[1].title)

        # Add 2 helpful votes the third document. It should be first now.
        rev = docs[2].current_revision
        helpful_vote(revision=rev, helpful=True, save=True)
        helpful_vote(revision=rev, helpful=True, save=True)
        docs[2].save()  # Votes don't trigger a reindex.
        self.refresh()
        cache.clear()  # documents_for() is cached
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(doc('#document-list > ul > li:first').text(), docs[2].title)

    def test_hot_topics(self):
        """Verifies the hot topics section."""
        # Create a product and the hot topics topic.
        p = product(save=True)
        hot = topic(slug=HOT_TOPIC_SLUG, save=True)

        # Create 7 hot documents.
        for i in range(7):
            doc = revision(is_approved=True, save=True).document
            doc.products.add(p)
            doc.topics.add(hot)

        # Create a not hot document.
        doc = revision(is_approved=True, save=True).document
        doc.products.add(p)

        self.refresh()

        # GET the product landing page and verify the content.
        url = reverse('products.product', args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(7, len(doc('#hot-topics li')))

    def test_subtopics(self):
        """Verifies subtopics appear on document listing page."""
        # Create a topic and product.
        t = topic(save=True)
        p = product(save=True)

        # Create a documents with the topic and product
        doc = revision(is_approved=True, save=True).document
        doc.topics.add(t)
        doc.products.add(p)

        self.refresh()

        # GET the page and verify no subtopics yet.
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(0, len(doc('ul.subtopics')))

        # Create a subtopic and verify it is listed
        topic(parent=t, save=True)
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, len(doc('ul.subtopics')))


class ProductViewsNewTopicsTestCase(ElasticTestCase):
    def setUp(self):
        super(ProductViewsNewTopicsTestCase, self).setUp()

        Flag.objects.create(name='new-topics', everyone=True).save()

    def test_products(self):
        """Verify that /products page renders products."""
        # Create some products.
        for i in range(3):
            product(save=True)

        # GET the products page and verify the content.
        r = self.client.get(reverse('products'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(4, len(doc('#products-and-services li')))

    def test_product_landing(self):
        """Verify that /products/<slug> page renders topics."""
        # Create a product.
        p = product(save=True)

        # Create some topics.
        new_topic(slug=HOT_TOPIC_SLUG, product=p, save=True)
        topics = []
        for i in range(11):
            topics.append(new_topic(product=p, save=True))

        # Create a document and assign the product and 10 topics.
        doc = revision(is_approved=True, save=True).document
        doc.products.add(p)
        for i in range(10):
            doc.new_topics.add(topics[i])

        self.refresh()

        # GET the product landing page and verify the content.
        url = reverse('products.product', args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(11, len(doc('#help-topics li')))
        eq_(p.slug, doc('#support-search input[name=product]').attr['value'])

    def test_document_listing(self):
        """Verify /products/<product slug>/<topic slug> renders articles."""
        # Create a topic and product.
        p = product(save=True)
        t1 = new_topic(product=p, save=True)

        # Create 3 documents with the topic and product and one without.
        for i in range(3):
            doc = revision(is_approved=True, save=True).document
            doc.new_topics.add(t1)
            doc.products.add(p)

        doc = revision(is_approved=True, save=True).document

        self.refresh()

        # GET the page and verify the content.
        url = reverse('products.documents', args=[p.slug, t1.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc('#document-list > ul > li')))
        eq_(p.slug, doc('#support-search input[name=product]').attr['value'])

    def test_document_listing_order(self):
        """Verify documents are listed in order of helpful votes."""
        # Create topic, product and documents.
        p = product(save=True)
        t = new_topic(product=p, save=True)
        docs = []
        for i in range(3):
            doc = revision(is_approved=True, save=True).document
            doc.new_topics.add(t)
            doc.products.add(p)
            docs.append(doc)

        # Add a helpful vote to the second document. It should be first now.
        rev = docs[1].current_revision
        helpful_vote(revision=rev, helpful=True, save=True)
        docs[1].save()  # Votes don't trigger a reindex.
        self.refresh()
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(doc('#document-list > ul > li:first').text(), docs[1].title)

        # Add 2 helpful votes the third document. It should be first now.
        rev = docs[2].current_revision
        helpful_vote(revision=rev, helpful=True, save=True)
        helpful_vote(revision=rev, helpful=True, save=True)
        docs[2].save()  # Votes don't trigger a reindex.
        self.refresh()
        cache.clear()  # documents_for() is cached
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(doc('#document-list > ul > li:first').text(), docs[2].title)

    def test_hot_topics(self):
        """Verifies the hot topics section."""
        # Create a product and the hot topics topic.
        p = product(save=True)
        hot = new_topic(slug=HOT_TOPIC_SLUG, product=p, save=True)

        # Create 7 hot documents.
        for i in range(7):
            doc = revision(is_approved=True, save=True).document
            doc.products.add(p)
            doc.new_topics.add(hot)

        # Create a not hot document.
        doc = revision(is_approved=True, save=True).document
        doc.products.add(p)

        self.refresh()

        # GET the product landing page and verify the content.
        url = reverse('products.product', args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(7, len(doc('#hot-topics li')))

    def test_subtopics(self):
        """Verifies subtopics appear on document listing page."""
        # Create a topic and product.
        p = product(save=True)
        t = new_topic(product=p, save=True)

        # Create a documents with the topic and product
        doc = revision(is_approved=True, save=True).document
        doc.new_topics.add(t)
        doc.products.add(p)

        self.refresh()

        # GET the page and verify no subtopics yet.
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(0, len(doc('ul.subtopics')))

        # Create a subtopic and verify it is listed
        new_topic(parent=t, product=p, save=True)
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, len(doc('ul.subtopics')))
