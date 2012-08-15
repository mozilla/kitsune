import mock
import waffle
from nose.tools import eq_
from pyquery import PyQuery as pq

from products.tests import product
from search.tests.test_es import ElasticTestCase
from sumo.urlresolvers import reverse
from topics.models import HOT_TOPIC_SLUG
from topics.tests import topic
from wiki.tests import revision


class ProductViewsTestCase(ElasticTestCase):
    @mock.patch.object(waffle, 'flag_is_active')
    def test_products(self, flag_is_active):
        """Verify that /products page renders products."""
        flag_is_active.return_value = True

        # Create some products.
        for i in range(3):
            product(save=True)

        # GET the products page and verify the content.
        r = self.client.get(reverse('products'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc('#products-and-services li')))

    @mock.patch.object(waffle, 'flag_is_active')
    def test_product_landing(self, flag_is_active):
        """Verify that /products/<slug> page renders topics."""
        flag_is_active.return_value = True

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
        eq_(10, len(doc('#help-topics li')))

    @mock.patch.object(waffle, 'flag_is_active')
    def test_document_listing(self, flag_is_active):
        """Verify /products/<product slug>/<topic slug> renders articles."""
        flag_is_active.return_value = True

        # Create a topic and product.
        t = topic(save=True)
        p = product(save=True)

        # Create 3 documents with the topic and product and one without.
        for i in range(3):
            doc = revision(is_approved=True, save=True).document
            doc.topics.add(t)
            doc.products.add(p)
        doc = revision(is_approved=True, save=True).document

        self.refresh()

        # GET the page and verify the content.
        url = reverse('products.documents', args=[p.slug, t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc('#document-list li')))

    @mock.patch.object(waffle, 'flag_is_active')
    def test_hot_topics(self, flag_is_active):
        """Verifies the hot topics section."""
        flag_is_active.return_value = True

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
