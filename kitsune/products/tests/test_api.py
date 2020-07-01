from nose.tools import eq_

from kitsune.products import api
from kitsune.products.tests import ProductFactory
from kitsune.products.tests import TopicFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


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


class TestTopicListView(TestCase):

    def test_it_works(self):
        p = ProductFactory()
        url = reverse('topic-list', kwargs={'product': p.slug})
        res = self.client.get(url)
        eq_(res.status_code, 200)

    def test_expected_output(self):
        p = ProductFactory()
        t1 = TopicFactory(product=p, visible=True, display_order=1)
        t2 = TopicFactory(product=p, visible=True, display_order=2)

        url = reverse('topic-list', kwargs={'product': p.slug})
        res = self.client.get(url)
        eq_(res.status_code, 200)

        eq_(res.data, {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                {
                    'title': t1.title,
                    'slug': t1.slug,
                },
                {
                    'title': t2.title,
                    'slug': t2.slug,
                },
            ],
        })
