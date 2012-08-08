import mock
import waffle
from nose.tools import eq_
from pyquery import PyQuery as pq

from products.tests import product
from search.tests.test_es import ElasticTestCase
from sumo.urlresolvers import reverse
from topics.tests import topic
from wiki.tests import revision


class ProductViewsTestCase(ElasticTestCase):
    @mock.patch.object(waffle, 'flag_is_active')
    def test_products(self, flag_is_active):
        """Verify that /products page renders products."""
        flag_is_active.return_value = True

        # Create some products
        for i in range(3):
            product(save=True)

        # GET the home page and verify the content
        r = self.client.get(reverse('products'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc('#products-and-services li')))

    @mock.patch.object(waffle, 'flag_is_active')
    def test_product_landing(self, flag_is_active):
        """Verify that /products/<slug> page renders topics."""
        flag_is_active.return_value = True

        # Create a product
        p = product(save=True)

        # Create some topics
        topics = []
        for i in range(11):
            topics.append(topic(save=True))

        # Create a document and assign the product and 10 topics.
        doc = revision(is_approved=True, save=True).document
        doc.products.add(p)
        for i in range(10):
            doc.topics.add(topics[i])

        self.refresh()

        # GET the topic page and verify the content
        url = reverse('products.product', args=[p.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(10, len(doc('#help-topics li')))
