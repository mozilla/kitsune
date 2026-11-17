import pyquery
from django.test.client import RequestFactory

from kitsune.sumo.paginator import EmptyPage, PageNotAnInteger
from kitsune.sumo.templatetags.jinja_helpers import paginator
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import paginate, simple_paginate


class PaginateTests(TestCase):
    def test_paginated_url_drops_the_page_param(self):
        for query, expected in (("q=bookmarks&page=2", "?q=bookmarks"), ("page=a", "?")):
            with self.subTest(query=query):
                request = RequestFactory().get(f"{reverse('search')}?{query}")
                paginated = paginate(request, list(range(100)))
                self.assertEqual(
                    paginated.url, request.build_absolute_uri(request.path) + expected
                )

    def test_paginator_filter(self):
        for query, items, per_page, expected_li in (("", 100, 9, 11), ("page=10", 200, 10, 13)):
            with self.subTest(query=query):
                request = RequestFactory().get(f"{reverse('search')}?{query}")
                pager = paginate(request, list(range(items)), per_page=per_page)
                doc = pyquery.PyQuery(paginator(pager))
                self.assertEqual(expected_li, len(doc("li")))


class SimplePaginatorTestCase(TestCase):
    rf = RequestFactory()

    def test_no_explicit_page(self):
        """No 'page' query param implies page 1."""
        request = self.rf.get("/questions")
        queryset = [{}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        self.assertEqual(1, page.number)

    def test_page_1_without_next(self):
        """Test page=1, doesn't have next page."""
        request = self.rf.get("/questions?page=1")
        queryset = [{}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        self.assertEqual(1, page.number)
        assert not page.has_previous()
        assert not page.has_next()

    def test_page_1_with_next(self):
        """Test page=1, has next page."""
        request = self.rf.get("/questions?page=1")
        queryset = [{}, {}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        self.assertEqual(1, page.number)
        assert not page.has_previous()
        assert page.has_next()

    def test_page_2_without_next(self):
        """Test page=2, doesn't have next page."""
        request = self.rf.get("/questions?page=2")
        queryset = [{}, {}, {}]
        page = simple_paginate(request, queryset, per_page=2)
        self.assertEqual(2, page.number)
        assert page.has_previous()
        assert not page.has_next()

    def test_page_2_empty(self):
        """Test page=1, has next page."""
        request = self.rf.get("/questions?page=2")
        queryset = [{}, {}]
        with self.assertRaises(EmptyPage):
            simple_paginate(request, queryset, per_page=2)

    def test_page_isnt_an_int(self):
        """Test page=1, has next page."""
        request = self.rf.get("/questions?page=foo")
        queryset = [{}, {}]
        with self.assertRaises(PageNotAnInteger):
            simple_paginate(request, queryset, per_page=2)
