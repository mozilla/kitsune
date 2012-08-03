import mock
import waffle
from nose.tools import eq_
from pyquery import PyQuery as pq

from products.tests import product
from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class ProductViewsTestCase(TestCase):
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
