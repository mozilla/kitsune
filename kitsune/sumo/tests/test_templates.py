from django.conf import settings
from django.template import engines as template_engines
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django.utils import translation

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.sumo.tests import LocalizingClient, TestCase
from kitsune.sumo.urlresolvers import reverse


def test_breadcrumb():
    """Make sure breadcrumb links start with /."""
    c = LocalizingClient()
    response = c.get(reverse('search'))

    doc = pq(response.content)
    href = doc('.breadcrumbs a')[0]
    eq_('/', href.attrib['href'][0])


class MockRequestTests(TestCase):
    """Base class for tests that need a mock request"""

    def setUp(self):
        super(MockRequestTests, self).setUp()
        request = RequestFactory()
        request.GET = {}
        request.LANGUAGE_CODE = 'en-US'
        self.request = request


class BaseTemplateTests(MockRequestTests):
    """Tests for base.html"""

    def setUp(self):
        super(BaseTemplateTests, self).setUp()
        self.template = 'base.html'

    def test_dir_ltr(self):
        """Make sure dir attr is set to 'ltr' for LTR language."""
        html = render_to_string(self.template, request=self.request)
        eq_('ltr', pq(html)('html').attr['dir'])

    def test_dir_rtl(self):
        """Make sure dir attr is set to 'rtl' for RTL language."""
        translation.activate('he')
        self.request.LANGUAGE_CODE = 'he'
        html = render_to_string(self.template, request=self.request)
        eq_('rtl', pq(html)('html').attr['dir'])
        translation.deactivate()

    def test_multi_feeds(self):
        """Ensure that multiple feeds are put into the page when set."""

        feed_urls = (('/feed_one', 'First Feed'),
                     ('/feed_two', 'Second Feed'),)

        doc = pq(render_to_string(self.template, {'feeds': feed_urls}, request=self.request))
        feeds = doc('link[type="application/atom+xml"]')
        eq_(2, len(feeds))
        eq_('First Feed', feeds[0].attrib['title'])
        eq_('Second Feed', feeds[1].attrib['title'])

    def test_readonly_attr(self):
        html = render_to_string(self.template, request=self.request)
        doc = pq(html)
        eq_('false', doc('body')[0].attrib['data-readonly'])

    @mock.patch.object(settings._wrapped, 'READ_ONLY', True)
    def test_readonly_login_link_disabled(self):
        """Ensure that login/register links are hidden in READ_ONLY."""
        html = render_to_string(self.template, request=self.request)
        doc = pq(html)
        eq_(0, len(doc('a.sign-out, a.sign-in')))

    @mock.patch.object(settings._wrapped, 'READ_ONLY', False)
    def test_not_readonly_login_link_enabled(self):
        """Ensure that login/register links are visible in not READ_ONLY."""
        html = render_to_string(self.template, request=self.request)
        doc = pq(html)
        assert len(doc('a.sign-out, a.sign-in')) > 0


class ErrorListTests(MockRequestTests):
    """Tests for errorlist.html, which renders form validation errors."""

    def test_escaping(self):
        """Make sure we escape HTML entities, lest we court XSS errors."""
        class MockForm(object):
            errors = True
            auto_id = 'id_'

            def visible_fields(self):
                return [{'errors': ['<"evil&ness-field">']}]

            def non_field_errors(self):
                return ['<"evil&ness-non-field">']

        source = ("""{% from "layout/errorlist.html" import errorlist %}"""
                  """{{ errorlist(form) }}""")
        template = template_engines['backend'].from_string(source)
        html = template.render({'form': MockForm()})
        assert '<"evil&ness' not in html
        assert '&lt;&#34;evil&amp;ness-field&#34;&gt;' in html
        assert '&lt;&#34;evil&amp;ness-non-field&#34;&gt;' in html
