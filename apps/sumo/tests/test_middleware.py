from django.http import HttpResponsePermanentRedirect

import mobility
from nose.tools import eq_
from test_utils import RequestFactory

from sumo.middleware import PlusToSpaceMiddleware, MobileSwitchMiddleware
from sumo.tests import TestCase


class TrailingSlashMiddlewareTestCase(TestCase):
    def test_no_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez')
        eq_(response.status_code, 404)

    def test_404_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez/')
        eq_(response.status_code, 404)

    def test_remove_trailing_slash(self):
        response = self.client.get(u'/en-US/home/?xxx=\xc3')
        eq_(response.status_code, 301)
        assert response['Location'].endswith('/en-US/home?xxx=%C3%83')


class PlusToSpaceTestCase(TestCase):

    rf = RequestFactory()
    ptsm = PlusToSpaceMiddleware()

    def test_plus_to_space(self):
        """Pluses should be converted to %20."""
        request = self.rf.get('/url+with+plus')
        response = self.ptsm.process_request(request)
        assert isinstance(response, HttpResponsePermanentRedirect)
        eq_('/url%20with%20plus', response['location'])

    def test_query_string(self):
        """Query strings should be maintained."""
        request = self.rf.get('/pa+th', {'a': 'b'})
        response = self.ptsm.process_request(request)
        eq_('/pa%20th?a=b', response['location'])

    def test_query_string_unaffected(self):
        """Pluses in query strings are not affected."""
        request = self.rf.get('/pa+th?var=a+b')
        response = self.ptsm.process_request(request)
        eq_('/pa%20th?var=a+b', response['location'])

    def test_pass_through(self):
        """URLs without a + should be left alone."""
        request = self.rf.get('/path')
        assert not self.ptsm.process_request(request)

    def test_with_locale(self):
        """URLs with a locale should keep it."""
        request = self.rf.get('/pa+th', {'a': 'b'})
        request.locale = 'ru'
        response = self.ptsm.process_request(request)
        eq_('/ru/pa%20th?a=b', response['location'])

    def test_smart_query_string(self):
        """The request QUERY_STRING might not be unicode."""
        request = self.rf.get(u'/pa+th')
        request.locale = 'ja'
        request.META['QUERY_STRING'] = 's=\xe3\x82\xa2'
        response = self.ptsm.process_request(request)
        eq_('/ja/pa%20th?s=%E3%82%A2', response['location'])


class MobileSwitchTestCase(TestCase):

    def test_mobile_0(self):
        response = self.client.get(u'/en-US/home?mobile=0')
        eq_(response.status_code, 200)
        # Make sure a mobile template was not used.
        assert not any('mobile' in t.name for t in response.templates)
        eq_(self.client.cookies.get(mobility.middleware.COOKIE).value, 'off')

    def test_mobile_1(self):
        response = self.client.get(u'/en-US/home?mobile=1', follow=True)
        eq_(response.status_code, 200)
        # Make sure a mobile template was used
        assert any('mobile' in t.name for t in response.templates)
        eq_(self.client.cookies.get(mobility.middleware.COOKIE).value, 'on')
