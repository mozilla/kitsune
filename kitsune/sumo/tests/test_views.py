from django.contrib.sites.models import Site
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.test import override_settings
from django.test.client import RequestFactory

from unittest import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.middleware import LocaleURLMiddleware
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.views import deprecated_redirect, redirect_to


class RedirectTests(TestCase):
    rf = RequestFactory()

    def test_redirect_to(self):
        resp = redirect_to(self.rf.get("/"), url="home", permanent=False)
        assert isinstance(resp, HttpResponseRedirect)
        eq_(reverse("home"), resp["location"])

    def test_redirect_permanent(self):
        resp = redirect_to(self.rf.get("/"), url="home")
        assert isinstance(resp, HttpResponsePermanentRedirect)
        eq_(reverse("home"), resp["location"])

    @mock.patch.object(Site.objects, "get_current")
    def test_deprecated_redirect(self, get_current):
        get_current.return_value.domain = "su.mo.com"
        req = self.rf.get("/en-US/")
        # Since we're rendering a template we need this to run.
        LocaleURLMiddleware().process_request(req)
        resp = deprecated_redirect(req, url="home")
        eq_(200, resp.status_code)
        doc = pq(resp.content)
        assert doc("meta[http-equiv=refresh]")
        refresh = doc("meta[http-equiv=refresh]")
        timeout, url = refresh.attr("content").split(";url=")
        eq_("10", timeout)
        eq_(reverse("home"), url)


class RobotsTestCase(TestCase):
    # Use the hard-coded URL because it's well-known.

    @override_settings(ENGAGE_ROBOTS=False)
    def test_disengaged(self):
        response = self.client.get("/robots.txt")
        eq_(b"User-Agent: *\nDisallow: /", response.content)
        eq_("text/plain", response["content-type"])

    @override_settings(ENGAGE_ROBOTS=True)
    def test_engaged(self):
        response = self.client.get("/robots.txt")
        eq_("text/plain", response["content-type"])
        assert len(response.content) > len("User-agent: *\nDisallow: /")
