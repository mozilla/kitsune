from django.http import HttpResponsePermanentRedirect
from django.test.client import RequestFactory

import mobility
from nose.tools import eq_

from kitsune.sumo.middleware import PlusToSpaceMiddleware, DetectMobileMiddleware
from kitsune.sumo.tests import TestCase, PyQuery as pq


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
        request.LANGUAGE_CODE = 'ru'
        response = self.ptsm.process_request(request)
        eq_('/ru/pa%20th?a=b', response['location'])

    def test_smart_query_string(self):
        """The request QUERY_STRING might not be unicode."""
        request = self.rf.get(u'/pa+th')
        request.LANGUAGE_CODE = 'ja'
        request.META['QUERY_STRING'] = 's=\xe3\x82\xa2'
        response = self.ptsm.process_request(request)
        eq_('/ja/pa%20th?s=%E3%82%A2', response['location'])


class MobileSwitchTestCase(TestCase):

    def test_mobile_0(self):
        response = self.client.get(u'/en-US/?mobile=0')
        eq_(response.status_code, 200)
        eq_(self.client.cookies.get(mobility.middleware.COOKIE).value, 'off')
        # Make sure a mobile template was not used.
        doc = pq(response.content)
        eq_(len(doc('#mobile-warning')), 1)
        eq_(len(doc('header.slide-on-exposed')), 0)

    def test_mobile_1(self):
        response = self.client.get(u'/en-US/?mobile=1', follow=True)
        eq_(response.status_code, 200)
        eq_(self.client.cookies.get(mobility.middleware.COOKIE).value, 'on')
        # Make sure a mobile template was used
        doc = pq(response.content)
        eq_(len(doc('#mobile-warning')), 0)
        eq_(len(doc('header.slide-on-exposed')), 1)


class MobileDetectTestCase(TestCase):

    def check(self, ua, should_be_mobile):
        request = RequestFactory().get('/en-US/home', HTTP_USER_AGENT=ua)
        DetectMobileMiddleware().process_request(request)

        if should_be_mobile:
            self.assertEqual(request.META['HTTP_X_MOBILE'], '1')
        else:
            assert 'HTTP_X_MOBILE' not in request.META

    def test_ipad_isnt_mobile(self):
        self.check(
            'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 '
            '(KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25',
            False)

    def test_android_tablet_isnt_mobile(self):
        self.check(
            'Mozilla/5.0 (Android; Tablet; rv:13.0) Gecko/13.0 Firefox/13.0',
            False)

    def test_desktop_firefox_isnt_mobile(self):
        self.check(
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:27.0) '
            'Gecko/20100101 Firefox/27.0',
            False)

    def test_firefoxos_is_mobile(self):
        self.check(
            'Mozilla/5.0 (Mobile; rv:18.0) Gecko/18.0 Firefox/18.0',
            True)

    def test_android_firefox_is_mobile(self):
        self.check(
            'Mozilla/5.0 (Android; Mobile; rv:13.0) Gecko/13.0 Firefox/13.0',
            True)

    def test_android_stock_is_mobile(self):
        self.check(
            'Mozilla/5.0 (Linux; U; Android 2.3; en-us) AppleWebKit/999+ '
            '(KHTML, like Gecko) Safari/999.9',
            True)

    def test_iphone_safari_is_mobile(self):
        self.check(
            'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) '
            'AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 '
            'Safari/528.16',
            True)
