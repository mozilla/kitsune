import mock
import waffle
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.products.tests import product
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.topics.tests import topic
from kitsune.wiki.tests import revision


class TopicViewsTestCase(ElasticTestCase):
    @mock.patch.object(waffle, 'flag_is_active')
    def test_topic_select_product(self, flag_is_active):
        """Verify that /topics/<slug>?selectproduct=1 renders products."""
        flag_is_active.return_value = True

        # Create a topic
        t = topic(save=True)

        # Create 3 products
        prods = []
        for i in range(3):
            prods.append(product(save=True))

        # Create a document and assign the topic and two products.
        doc = revision(is_approved=True, save=True).document
        doc.topics.add(t)
        doc.products.add(prods[0])
        doc.products.add(prods[1])

        self.refresh()

        # GET the topic page and verify the content
        url = reverse('topics.topic', args=[t.slug])
        url = urlparams(url, selectproduct=1)
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(2, len(doc('#products-and-services li')))

    @mock.patch.object(waffle, 'flag_is_active')
    def test_topic_document_listing(self, flag_is_active):
        """Verify that /topics/<slug> renders articles."""
        flag_is_active.return_value = True

        # Create a topic
        t = topic(save=True)

        # Create 3 documents with the topic and one without
        for i in range(3):
            doc = revision(is_approved=True, save=True).document
            doc.topics.add(t)
        doc = revision(is_approved=True, save=True).document

        self.refresh()

        # GET the topic page and verify the content
        url = reverse('topics.topic', args=[t.slug])
        r = self.client.get(url, follow=True)
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(3, len(doc('#document-list li')))
