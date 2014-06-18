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
