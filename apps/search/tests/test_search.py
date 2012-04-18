"""
Tests for the search view that aren't search system specific
"""
import json

import jingo
from nose.tools import eq_

from django.conf import settings

from sumo.tests import LocalizingClient, ElasticTestCase
from sumo.urlresolvers import reverse
from wiki.tests import document, revision


def render(s, context):
    t = jingo.env.from_string(s)
    return t.render(context)


class SearchTest(ElasticTestCase):
    client_class = LocalizingClient

    def test_content(self):
        """Ensure template is rendered with no errors for a common search"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_content_mobile(self):
        """Ensure mobile template is rendered."""
        self.client.cookies[settings.MOBILE_COOKIE] = 'on'
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_search_type_param(self):
        """Ensure that invalid values for search type (a=)
        does not cause errors"""
        response = self.client.get(reverse('search'), {'a': 'dontdie'})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_headers(self):
        """Verify caching headers of search forms and search results"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response
        response = self.client.get(reverse('search'))
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response

    def test_page_invalid(self):
        """Ensure non-integer param doesn't throw exception."""
        doc = document(
            title=u'How to fix your audio',
            locale=u'en-US',
            category=10,
            save=True)
        doc.tags.add(u'desktop')
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {
                'a': 1, 'format': 'json', 'page': 'invalid'
                })
        eq_(200, response.status_code)
        eq_(1, json.loads(response.content)['total'])
