from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.tests import MobileTestCase, TestCase
from sumo.urlresolvers import reverse


class MobileHomeTests(MobileTestCase):
    def test_desktop_home_for_mobile(self):
        r = self.client.get(reverse('home'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/home.html')
        doc = pq(r.content)
        eq_('desktop', doc('#search input[name="q_tags"]')[0].attrib['value'])
        eq_('desktop', doc('#search input[name="product"]')[0].attrib['value'])

    def test_mobile_home_for_mobile(self):
        r = self.client.get(reverse('home.mobile'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/mobile.html')
        doc = pq(r.content)
        eq_('mobile', doc('#search input[name="q_tags"]')[0].attrib['value'])
        eq_('mobile', doc('#search input[name="product"]')[0].attrib['value'])

    def test_sync_home_for_mobile(self):
        r = self.client.get(reverse('home.sync'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/sync.html')
        doc = pq(r.content)
        eq_('sync', doc('#search input[name="q_tags"]')[0].attrib['value'])
        eq_('sync', doc('#search input[name="product"]')[0].attrib['value'])

    def test_fxhome_home_for_mobile(self):
        r = self.client.get(reverse('home.fxhome'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/fxhome.html')
        doc = pq(r.content)
        eq_('FxHome', doc('#search input[name="q_tags"]')[0].attrib['value'])
        eq_('FxHome', doc('#search input[name="product"]')[0].attrib['value'])

    def test_marketplace_home_for_mobile(self):
        r = self.client.get(reverse('home.marketplace'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/marketplace.html')
        doc = pq(r.content)
        eq_('marketplace',
            doc('#search input[name="product"]')[0].attrib['value'])
        eq_('1', doc('#search input[name="w"]')[0].attrib['value'])


class HomeRedirects(TestCase):
    def test_default_redirect(self):
        """/ redirects to /home"""
        response = self.client.get(reverse('home.default', locale='en-US'),
                                   follow=False)
        eq_(301, response.status_code)
        eq_('http://testserver/en-US/home', response['location'])
