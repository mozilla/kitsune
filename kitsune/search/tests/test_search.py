"""
Tests for the search view that aren't search system specific
"""
import json

from django.conf import settings

import jingo
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.products.tests import product
from kitsune.questions.tests import question, answer, answervote
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.tests import document, revision


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
            'a': 1,
            'format': 'json',
            'page': 'invalid'
        })
        eq_(200, response.status_code)
        eq_(1, json.loads(response.content)['total'])

    def test_clean_excerpt(self):
        """Ensure we clean html out of excerpts."""
        q = question(title='audio',
                     content='<script>alert("hacked");</script>', save=True)
        a = answer(question=q, save=True)
        answervote(answer=a, helpful=True, save=True)

        self.refresh()

        response = self.client.get(reverse('search'), {'q': 'audio'})
        eq_(200, response.status_code)

        doc = pq(response.content)
        assert 'script' not in doc('div.result').text()

    def test_ga_zero_results_event(self):
        """If there are no results, verify ga-push data attr on body."""
        doc = document(title=u'audio', locale=u'en-US', category=10, save=True)
        doc.products.add(product(title=u'firefox', slug=u'desktop', save=True))
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # If there are results, data-ga-push should be an empty list.
        response = self.client.get(reverse('search'), {'q': 'audio'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('[]', doc('body').attr('data-ga-push'))

        # If there are no results, then Zero Search Results event is there.
        response = self.client.get(reverse('search'), {'q': 'piranha'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert '"Zero Search Results"' in doc('body').attr('data-ga-push')

    def test_fallback_for_zero_results(self):
        """If there are no results, fallback to a list of top articles."""
        firefox = product(title=u'firefox', slug=u'desktop', save=True)
        doc = document(title=u'audio1', locale=u'en-US', category=10,
                       save=True)
        doc.products.add(firefox)
        revision(document=doc, is_approved=True, save=True)
        doc = document(title=u'audio2', locale=u'en-US', category=10,
                       save=True)
        doc.products.add(firefox)
        revision(document=doc, is_approved=True, save=True)

        self.refresh()

        # Verify there are no real results but 2 fallback results are rendered
        response = self.client.get(reverse('search'), {'q': 'piranha'})
        eq_(200, response.status_code)

        assert "We couldn't find any results for" in response.content
        doc = pq(response.content)
        eq_(2, len(doc('#search-results .result')))

    def test_search_products(self):
        p = product(title=u'Product One', slug='product', save=True)
        doc1 = document(title=u'cookies', locale='en-US', category=10,
                        save=True)
        revision(document=doc1, is_approved=True, save=True)
        doc1.products.add(p)
        doc1.save()

        self.refresh()

        response = self.client.get(reverse('search'), {'a': '1',
                                                       'product': 'product',
                                                       'q': 'cookies',
                                                       'w': '1'})

        assert "We couldn't find any results for" not in response.content
        eq_(200, response.status_code)
        assert 'Product One' in response.content

    def test_search_multiple_products(self):
        p = product(title=u'Product One', slug='product-one', save=True)
        p2 = product(title=u'Product Two', slug='product-two', save=True)
        doc1 = document(title=u'cookies', locale='en-US', category=10,
                        save=True)
        revision(document=doc1, is_approved=True, save=True)
        doc1.products.add(p)
        doc1.products.add(p2)
        doc1.save()

        self.refresh()

        response = self.client.get(reverse('search'), {
            'a': '1',
            'product': ['product-one', 'product-two'],
            'q': 'cookies',
            'w': '1',
        })

        assert "We couldn't find any results for" not in response.content
        eq_(200, response.status_code)
        assert 'Product One, Product Two' in response.content
