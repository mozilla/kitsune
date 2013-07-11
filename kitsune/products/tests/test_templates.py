from datetime import datetime, timedelta

from django.core.cache import cache

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq
from waffle.models import Flag

from kitsune.products.tests import product, topic
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.tags.tests import tag
from kitsune.topics.models import HOT_TOPIC_SLUG
from kitsune.wiki.tests import revision, helpful_vote
from kitsune.wiki import views as wiki_views
from kitsune.questions.tests import question


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
        topic(slug=HOT_TOPIC_SLUG, product=p, save=True)
        topics = []
        for i in range(11):
            topics.append(topic(product=p, save=True))

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
        p = product(save=True)
        t1 = topic(product=p, save=True)

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
        p = product(save=True)
        t = topic(product=p, save=True)
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
        eq_(doc('#document-list > ul > li:first-child > a').text(), docs[1].title)

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
        eq_(doc('#document-list > ul > li:first-child > a').text(), docs[2].title)

    def test_hot_topics(self):
        """Verifies the hot topics section."""
        # Create a product and the hot topics topic.
        p = product(save=True)
        hot = topic(slug=HOT_TOPIC_SLUG, product=p, save=True)

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

    def test_hot_questions(self):
        """Verifies that hot questions show up in the hot topics section."""

        # Create a product and the hot topics topic.
        p = product(save=True)
        hot_tag = tag(name='hot', slug=HOT_TOPIC_SLUG, save=True)
        # Create a flag, since this code is flagged off by default.
        Flag.objects.create(name='hot_questions', everyone=True)

        # Create 4 hot questions.
        titles = ['apple', 'banana', 'cherry', 'date']
        timestamp = datetime.now() - timedelta(days=7)
        for i in range(4):
            q = question(title=titles[i], created=timestamp, save=True)
            q.products.add(p)
            q.tags.add(hot_tag)
            timestamp += timedelta(days=1)

        # Create a non-hot document.
        q = question(title='elderberry', save=True)
        q.products.add(p)

        # GET the product landing page and verify the content.
        url = reverse('products.product', args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)

        doc = pq(r.content)
        eq_(3, len(doc('#hot-topics li.question')))

        # Only the 3 newest hot topics should show up.
        assert 'apple' not in r.content
        assert 'banana' in r.content
        assert 'cherry' in r.content
        assert 'date' in r.content
        # Non-hot topics should not show up.
        assert 'elderberry' not in r.content

    def test_subtopics(self):
        """Verifies subtopics appear on document listing page."""
        # Create a topic and product.
        p = product(save=True)
        t = topic(product=p, save=True)

        # Create a documents with the topic and product
        doc = revision(is_approved=True, save=True).document
        doc.topics.add(t)
        doc.products.add(p)

        self.refresh()

        # GET the page and verify no subtopics yet.
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        pqdoc = pq(r.content)
        eq_(0, len(pqdoc('ul.subtopics')))

        # Create a subtopic, it still shouldn't show up because no
        # articles are assigned.
        subtopic = topic(parent=t, product=p, save=True)
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        pqdoc = pq(r.content)
        eq_(0, len(pqdoc('ul.subtopics')))

        # Add a document to the subtopic, now it should appear.
        doc.topics.add(subtopic)
        self.refresh()

        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        pqdoc = pq(r.content)
        eq_(1, len(pqdoc('ul.subtopics')))
