import json

import django
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.test.client import RequestFactory

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.middleware import LocaleURLMiddleware
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.views import deprecated_redirect, redirect_to


class RedirectTests(TestCase):
    rf = RequestFactory()

    def test_redirect_to(self):
        resp = redirect_to(self.rf.get('/'), url='home', permanent=False)
        assert isinstance(resp, HttpResponseRedirect)
        eq_(reverse('home'), resp['location'])

    def test_redirect_permanent(self):
        resp = redirect_to(self.rf.get('/'), url='home')
        assert isinstance(resp, HttpResponsePermanentRedirect)
        eq_(reverse('home'), resp['location'])

    def test_redirect_kwargs(self):
        resp = redirect_to(self.rf.get('/'), url='users.confirm_email',
                           activation_key='1234')
        eq_(reverse('users.confirm_email', args=['1234']),
            resp['location'])

    @mock.patch.object(Site.objects, 'get_current')
    def test_deprecated_redirect(self, get_current):
        get_current.return_value.domain = 'su.mo.com'
        req = self.rf.get('/en-US/')
        # Since we're rendering a template we need this to run.
        LocaleURLMiddleware().process_request(req)
        resp = deprecated_redirect(req, url='home')
        eq_(200, resp.status_code)
        doc = pq(resp.content)
        assert doc('meta[http-equiv=refresh]')
        refresh = doc('meta[http-equiv=refresh]')
        timeout, url = refresh.attr('content').split(';url=')
        eq_('10', timeout)
        eq_(reverse('home'), url)


class RobotsTestCase(TestCase):
    # Use the hard-coded URL because it's well-known.
    old_setting = settings.ENGAGE_ROBOTS

    def tearDown(self):
        settings.ENGAGE_ROBOTS = self.old_setting

    def test_disengaged(self):
        settings.ENGAGE_ROBOTS = False
        response = self.client.get('/robots.txt')
        eq_('User-Agent: *\nDisallow: /', response.content)
        eq_('text/plain', response['content-type'])

    def test_engaged(self):
        settings.ENGAGE_ROBOTS = True
        response = self.client.get('/robots.txt')
        eq_('text/plain', response['content-type'])
        assert len(response.content) > len('User-agent: *\nDisallow: /')


class VersionCheckTests(TestCase):
    url = reverse('sumo.version')

    def _is_forbidden(self, url):
        res = self.client.get(url)
        eq_(403, res.status_code)
        eq_('', res.content)

    @mock.patch.object(settings._wrapped, 'VERSION_CHECK_TOKEN', None)
    def token_is_none(self):
        self._is_forbidden(self.url)
        self._is_forbidden(urlparams(self.url, token='foo'))

    @mock.patch.object(settings._wrapped, 'VERSION_CHECK_TOKEN', 'foo')
    def token_is_wrong(self):
        self._is_forbidden(urlparams(self.url, token='bar'))

    @mock.patch.object(settings._wrapped, 'VERSION_CHECK_TOKEN', 'foo')
    def token_is_right(self):
        res = self.client.get(urlparams(self.url, token='foo'))
        eq_(200, res.status_code)
        versions = json.loads(res.content)
        eq_('.'.join(map(str, django.VERSION)), versions['django'])


class ForceErrorTests(TestCase):
    url = reverse('sumo.error')

    @mock.patch.object(settings._wrapped, 'STAGE', True)
    def test_error(self):
        """On STAGE servers, be able to force an error."""
        try:
            self.client.get(self.url)
            self.fail()
        except NameError:
            pass

    @mock.patch.object(settings._wrapped, 'STAGE', False)
    def test_hidden(self):
        """On a non-STAGE server, no forcing errors."""
        res = self.client.get(self.url)
        eq_(404, res.status_code)
