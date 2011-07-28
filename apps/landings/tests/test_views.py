from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.tests import MobileTestCase, TestCase
from sumo.urlresolvers import reverse


class MobileHomeTests(MobileTestCase):
    def test_desktop_home_for_mobile(self):
        r = self.client.get(reverse('home'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/home.html')

    def test_mobile_home_for_mobile(self):
        r = self.client.get(reverse('home.mobile'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/mobile.html')
        doc = pq(r.content)
        eq_('mobile', doc('#search input[name="q_tags"]')[0].attrib['value'])
        eq_('mobile', doc('#search input[name="tags"]')[0].attrib['value'])

    def test_sync_home_for_mobile(self):
        r = self.client.get(reverse('home.sync'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/sync.html')

    def test_fxhome_home_for_mobile(self):
        r = self.client.get(reverse('home.fxhome'), follow=True)
        eq_(r.status_code, 200)
        self.assertTemplateUsed(r, 'landings/mobile/fxhome.html')


class HomeRedirects(TestCase):
    def test_default_redirect(self):
        """/ redirects to /home"""
        response = self.client.get(reverse('home.default', locale='en-US'),
                                   follow=False)
        eq_(301, response.status_code)
        eq_('http://testserver/en-US/home', response['location'])
