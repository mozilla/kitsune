from django.test.client import RequestFactory

import pyquery
from nose.tools import eq_, raises

from kitsune.sumo.templatetags.jinja_helpers import paginator
from kitsune.sumo.paginator import EmptyPage, PageNotAnInteger
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import paginate, simple_paginate


def test_paginated_url():
    """Avoid duplicating page param in pagination."""
    url = '%s?%s' % (reverse('search'), 'q=bookmarks&page=2')
    request = RequestFactory().get(url)
    queryset = [{}, {}]
    paginated = paginate(request, queryset)
    eq_(paginated.url,
        request.build_absolute_uri(request.path) + '?q=bookmarks')


def test_invalid_page_param():
    url = '%s?%s' % (reverse('search'), 'page=a')
    request = RequestFactory().get(url)
    queryset = range(100)
    paginated = paginate(request, queryset)
    eq_(paginated.url,
        request.build_absolute_uri(request.path) + '?')


def test_paginator_filter():

    # Correct number of <li>s on page 1.
    url = reverse('search')
    request = RequestFactory().get(url)
    pager = paginate(request, range(100), per_page=9)
    html = paginator(pager)
    doc = pyquery.PyQuery(html)
    eq_(11, len(doc('li')))

    # Correct number of <li>s in the middle.
    url = '%s?%s' % (reverse('search'), 'page=10')
    request = RequestFactory().get(url)
    pager = paginate(request, range(200), per_page=10)
    html = paginator(pager)
    doc = pyquery.PyQuery(html)
    eq_(13, len(doc('li')))


class SimplePaginatorTestCase(TestCase):

    rf = RequestFactory()

    def test_no_explicit_page(self):
        """No 'page' query param implies page 1."""
        request = self.rf.get('/questions')
        queryset = [{}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        eq_(1, page.number)

    def test_page_1_without_next(self):
        """Test page=1, doesn't have next page."""
        request = self.rf.get('/questions?page=1')
        queryset = [{}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        eq_(1, page.number)
        assert not page.has_previous()
        assert not page.has_next()

    def test_page_1_with_next(self):
        """Test page=1, has next page."""
        request = self.rf.get('/questions?page=1')
        queryset = [{}, {}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        eq_(1, page.number)
        assert not page.has_previous()
        assert page.has_next()

    def test_page_2_without_next(self):
        """Test page=2, doesn't have next page."""
        request = self.rf.get('/questions?page=2')
        queryset = [{}, {}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        eq_(2, page.number)
        assert page.has_previous()
        assert not page.has_next()

    @raises(EmptyPage)
    def test_page_2_empty(self):
        """Test page=1, has next page."""
        request = self.rf.get('/questions?page=2')
        queryset = [{}, {}]
        simple_paginate(request, queryset, per_page=2)

    @raises(PageNotAnInteger)
    def test_page_isnt_an_int(self):
        """Test page=1, has next page."""
        request = self.rf.get('/questions?page=foo')
        queryset = [{}, {}]
        simple_paginate(request, queryset, per_page=2)
