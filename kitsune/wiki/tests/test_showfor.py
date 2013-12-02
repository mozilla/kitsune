# -*- coding: utf-8 -*-
from nose.tools import eq_

from kitsune.products.tests import product, version
from kitsune.sumo.tests import TestCase
from kitsune.wiki.showfor import showfor_data


class ShowforDataTests(TestCase):
    """Tests for notifications sent during revision review"""

    def test_all_versions(self):
        """Test that products with visible=False are in the showfor data."""
        prod = product(save=True)
        v1 = version(visible=True, product=prod, save=True)
        v2 = version(visible=False, product=prod, save=True)

        data = showfor_data([prod])

        eq_(len(data['versions'][prod.slug]), 2)
