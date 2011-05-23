from django.conf import settings

import mock
from nose.tools import eq_
from test_utils import RequestFactory

from sumo.tests import TestCase
from users.middleware import StaySecureMiddleware


class StaySecureTests(TestCase):
    rf = RequestFactory()
    ssm = StaySecureMiddleware()

    @mock.patch.object(settings._wrapped, 'SESSION_COOKIE_SECURE', True)
    def test_redirect_if_session(self):
        get = self.rf.get('/foo')
        assert not get.is_secure()
        resp = self.ssm.process_request(get)
        assert not resp

        get.COOKIES[settings.SESSION_EXISTS_COOKIE] = u'1'
        resp = self.ssm.process_request(get)
        assert resp
        eq_(302, resp.status_code)
        assert resp['location'].startswith('https://')

    @mock.patch.object(settings._wrapped, 'SESSION_COOKIE_SECURE', True)
    def test_maintain_query_string(self):
        get = self.rf.get('/foo?bar=baz')
        assert not get.is_secure()
        get.COOKIES[settings.SESSION_EXISTS_COOKIE] = u'1'
        resp = self.ssm.process_request(get)
        assert resp
        assert resp['location'].endswith('bar=baz')
