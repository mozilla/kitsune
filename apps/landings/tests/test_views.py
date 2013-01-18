from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.tests import MobileTestCase, TestCase
from sumo.urlresolvers import reverse


class MobileHomeTests(MobileTestCase):
    def test_sync_home_for_mobile(self):
        self._check_template('home.sync', 'landings/mobile/sync.html')

    def test_marketplace_home_for_mobile(self):
        r = self._check_template(
            'home.marketplace', 'landings/mobile/marketplace.html')
        doc = pq(r.content)
        eq_('1', doc('#search input[name="w"]')[0].attrib['value'])

    def test_firefox_home_for_mobile(self):
        self._check_template('home.firefox', 'landings/mobile/firefox.html')

    def test_ask_home_for_mobile(self):
        self._check_template('home.ask', 'landings/mobile/ask.html')

    def test_participate_home_for_mobile(self):
        self._check_template(
            'home.participate', 'landings/mobile/participate.html')

    def test_feedback_home_for_mobile(self):
        self._check_template('home.feedback', 'landings/mobile/feedback.html')

    def _check_template(self, url_name, template):
        r = self.client.get(reverse(url_name), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, template)
        return r


class RootRedirectTests(TestCase):
    def test_default_redirect(self):
        """/ redirects to /home"""
        response = self.client.get(reverse('home.default', locale='en-US'),
                                   follow=False)
        eq_(302, response.status_code)
        eq_('http://testserver/en-US/home', response['location'])


class RootRedirectForMobileTests(MobileTestCase):
    def test_default_redirect(self):
        """/ redirects to /mobile"""
        response = self.client.get(reverse('home.default', locale='en-US'),
                                   follow=False)
        eq_(302, response.status_code)
        eq_('http://testserver/en-US/products', response['location'])
