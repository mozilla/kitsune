from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.products.tests import product
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.urlresolvers import reverse


class HomeTestCase(ElasticTestCase):
    def test_home(self):
        """Verify that home page renders products."""

        # Create some topics and products
        for i in range(4):
            product(save=True)

        # GET the home page and verify the content
        r = self.client.get(reverse('home'), follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(5, len(doc('#products-and-services li')))
