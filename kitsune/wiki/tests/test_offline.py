from nose.tools import eq_

from kitsune.sumo.tests import TestCase

from kitsune.wiki.offline import (
    serialize_document_for_offline,
    bundle_for_product,
    merge_bundles
)
from wiki.tests import document, revision

class BundleGenerationTestCase(TestCase):
    """Test the generation of bundles for oSUMO"""
    def test_document_dump(self):
        d = document(title='test')
