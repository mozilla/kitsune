from pyquery import PyQuery as pq

from kitsune.products.tests import ProductFactory
from kitsune.search.tests import Elastic7TestCase
from kitsune.sumo.urlresolvers import reverse


class HomeTestCase(Elastic7TestCase):
    search_tests = True

    def test_home(self):
        """Verify that home page renders products."""

        # Create some topics and products
        ProductFactory.create_batch(4)

        # GET the home page and verify the content
        r = self.client.get(reverse("home"), follow=True)
        self.assertEqual(200, r.status_code)
        doc = pq(r.content)
        self.assertEqual(4, len(doc(".card--product")))
