from nose.tools import eq_

from kitsune.products.tests import product, topic
from kitsune.sumo.tests import TestCase


class TopicModelTests(TestCase):

    def test_path(self):
        """Verify that the path property works."""
        p = product(slug='p', save=True)
        t1 = topic(product=p, slug='t1', save=True)
        t2 = topic(product=p, slug='t2', parent=t1, save=True)
        t3 = topic(product=p, slug='t3', parent=t2, save=True)

        eq_(t1.path, [t1.slug])
        eq_(t2.path, [t1.slug, t2.slug])
        eq_(t3.path, [t1.slug, t2.slug, t3.slug])

    def test_absolute_url(self):
        p = product(save=True)
        t = topic(product=p, save=True)
        expected = '/products/{p}/{t}'.format(p=p.slug, t=t.slug)
        actual = t.get_absolute_url()
        eq_(actual, expected)

    def test_absolute_url_subtopic(self):
        p = product(save=True)
        t1 = topic(product=p, save=True)
        t2 = topic(parent=t1, product=p, save=True)
        expected = '/products/{p}/{t1}/{t2}'.format(p=p.slug, t1=t1.slug, t2=t2.slug)
        actual = t2.get_absolute_url()
        eq_(actual, expected)


class ProductModelTests(TestCase):

    def test_absolute_url(self):
        p = product(save=True)
        expected = '/products/{p}'.format(p=p.slug)
        actual = p.get_absolute_url()
        eq_(actual, expected)
