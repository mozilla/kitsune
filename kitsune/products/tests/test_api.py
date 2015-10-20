from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.products import api
from kitsune.products.tests import ProductFactory


class TestProductSerializerSerialization(TestCase):

    def test_product_with_no_image_doesnt_blow_up(self):
        p = ProductFactory(image=None)
        serializer = api.ProductSerializer()
        native = serializer.to_representation(p)
        eq_(native['image'], None)

    def test_product_with_image_works(self):
        # The factory will make a fictional image for the product
        p = ProductFactory()
        serializer = api.ProductSerializer()
        data = serializer.to_representation(p)
        eq_(data['image'], p.image.url)
