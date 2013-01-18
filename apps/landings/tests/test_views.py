from nose.tools import eq_

from sumo.tests import MobileTestCase, TestCase
from sumo.urlresolvers import reverse


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
