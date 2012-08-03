from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.tests import MobileTestCase, TestCase
from sumo.urlresolvers import reverse


class MobileHomeTests(MobileTestCase):
    def test_desktop_home_for_mobile(self):
        r = self._check_template('home', 'landings/mobile/old-home.html')
        doc = pq(r.content)
        eq_('desktop', doc('#search input[name="q_tags"]')[0].attrib['value'])
        eq_('firefox',
            doc('#search input[name="product"]')[0].attrib['value'])

    def test_mobile_home_for_mobile(self):
        r = self._check_template('home.mobile', 'landings/mobile/mobile.html')
        doc = pq(r.content)
        eq_('mobile', doc('#search input[name="q_tags"]')[0].attrib['value'])
        eq_('mobile', doc('#search input[name="product"]')[0].attrib['value'])

    def test_sync_home_for_mobile(self):
        self._check_template('home.sync', 'landings/mobile/sync.html')

    def test_fxhome_home_for_mobile(self):
        self._check_template('home.fxhome', 'landings/mobile/fxhome.html')

    def test_marketplace_home_for_mobile(self):
        r = self._check_template(
            'home.marketplace', 'landings/mobile/marketplace.html')
        doc = pq(r.content)
        eq_('1', doc('#search input[name="w"]')[0].attrib['value'])

    def test_firefox_home_for_mobile(self):
        self._check_template('home.firefox', 'landings/mobile/firefox.html')

    def test_products_home_for_mobile(self):
        self._check_template('products', 'landings/mobile/products.html')

    def test_kb_home_for_mobile(self):
        self._check_template('home.kb', 'landings/mobile/kb.html')

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
        eq_('http://testserver/en-US/mobile', response['location'])
