from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.tests import TestCase
from sumo.urlresolvers import reverse


class MobileHomeTestCase(TestCase):
    def test_top_text(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        self.assertContains(response, 'Firefox for Mobile')

    def test_no_plugin_check(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        self.assertNotContains(response, 'run an instant check')

    def test_search_params(self):
        response = self.client.get(reverse('home.mobile'), follow=True)
        doc = pq(response.content)
        eq_('mobile',
            doc('#support-search input[name="q_tags"]')[0].attrib['value'])
        eq_('mobile',
            doc('#support-search input[name="product"]')[0].attrib['value'])
