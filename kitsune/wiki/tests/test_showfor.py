# -*- coding: utf-8 -*-

from kitsune.products.tests import ProductFactory, VersionFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.showfor import showfor_data


class ShowforDataTests(TestCase):
    """Tests for notifications sent during revision review"""

    def test_all_versions(self):
        """Test that products with visible=False are in the showfor data."""
        prod = ProductFactory()
        VersionFactory(visible=True, product=prod)
        VersionFactory(visible=False, product=prod)

        data = showfor_data([prod])

        self.assertEqual(len(data["versions"][prod.slug]), 2)
