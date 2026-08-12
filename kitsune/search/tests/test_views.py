import json
from dataclasses import replace
from unittest import mock

from django.test.utils import override_settings
from pyquery import PyQuery as pq
from waffle.testutils import override_switch

from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory, QuestionLocaleFactory
from kitsune.search.hybrid import HybridSearchResults
from kitsune.search.tests import ElasticTestCase
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse

HYBRID_DOCUMENT = {
    "type": "document",
    "url": "/kb/article",
    "title": "Article",
    "search_summary": "Summary",
    "rank": 11,
    "evidence_locale": "en-US",
    "display_locale": "en-US",
    "locale_fallback": False,
}

HYBRID_RESULT = HybridSearchResults(
    results=(HYBRID_DOCUMENT,),
    approximate_total=1,
    page=1,
    has_previous=False,
    has_next=False,
    mode="hybrid",
    degraded=False,
    failed_shards=0,
    es_took_ms=2,
    total_ms=3,
    embedding_ms=1,
    query_vector_cache_hit=False,
    fallback_reason=None,
)


class TestSearchSEO(ElasticTestCase):
    """Test SEO-related aspects of the SUMO search view."""

    def test_simple_search(self):
        """
        Test SEO-related response for search.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?q=firefox")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("text/html" in response["content-type"])
        doc = pq(response.content)
        self.assertEqual(doc('meta[name="robots"]').attr("content"), "noindex, nofollow")

    def test_simple_search_json(self):
        """
        Test SEO-related response for search when JSON is requested.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?format=json&q=firefox")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("application/json" in response["content-type"])
        self.assertTrue("x-robots-tag" in response)
        self.assertEqual(response["x-robots-tag"], "noindex, nofollow")

    def test_invalid_search(self):
        """
        Test SEO-related response for invalid search.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?abc=firefox")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("text/html" in response["content-type"])
        doc = pq(response.content)
        self.assertEqual(doc('meta[name="robots"]').attr("content"), "noindex, nofollow")

    def test_invalid_search_json(self):
        """
        Test SEO-related response for invalid search when JSON is requested.
        """
        url = reverse("search", locale="en-US")
        response = self.client.get(f"{url}?format=json&abc=firefox")
        self.assertEqual(response.status_code, 400)
        self.assertTrue("application/json" in response["content-type"])
        self.assertEqual(json.loads(response.content), {"error": "Invalid search data."})
        self.assertTrue("x-robots-tag" in response)
        self.assertEqual(response["x-robots-tag"], "noindex")


class TestSearchSupportCard(ElasticTestCase):
    """Test that the 'Still need help?' card respects product-support config."""

    def _search_json(self, product_slug=None):
        url = reverse("search", locale="en-US")
        params = "format=json&q=zzzznotfound"
        if product_slug:
            params += f"&product={product_slug}"
        response = self.client.get(f"{url}?{params}")
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def test_no_product_shows_support_url(self):
        data = self._search_json()
        self.assertEqual(data["support_aaq_url"], reverse("questions.aaq_step1", locale="en-US"))

    def test_product_with_forum_support_shows_url(self):
        product = ProductFactory(slug="test-product", visible=True)
        locale = QuestionLocaleFactory(locale="en-US")
        aaq_config = AAQConfigFactory(enabled_locales=[locale])
        ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            is_active=True,
        )
        data = self._search_json(product_slug="test-product")
        self.assertEqual(
            data["support_aaq_url"],
            reverse(
                "questions.aaq_step3", locale="en-US", kwargs={"product_slug": "test-product"}
            ),
        )

    def test_product_with_zendesk_support_shows_url(self):
        product = ProductFactory(slug="test-zendesk", visible=True)
        ProductSupportConfigFactory(
            product=product,
            zendesk_config=ZendeskConfigFactory(),
            is_active=True,
        )
        data = self._search_json(product_slug="test-zendesk")
        self.assertEqual(
            data["support_aaq_url"],
            reverse(
                "questions.aaq_step3", locale="en-US", kwargs={"product_slug": "test-zendesk"}
            ),
        )

    def test_subscription_only_redirect_shows_redirect_url(self):
        redirect_product = ProductFactory(slug="test-redirect-target", visible=True)
        product = ProductFactory(slug="test-redirect", visible=True)
        ProductSupportConfigFactory(
            product=product,
            zendesk_config=ZendeskConfigFactory(),
            is_active=True,
            subscription_only=True,
            unsubscribed_redirect_product=redirect_product,
        )
        data = self._search_json(product_slug="test-redirect")
        self.assertEqual(
            data["support_aaq_url"],
            reverse(
                "questions.aaq_step2",
                locale="en-US",
                kwargs={"product_slug": "test-redirect-target"},
            ),
        )

    def test_subscription_only_hide_no_support_url(self):
        product = ProductFactory(slug="test-sub", visible=True)
        ProductSupportConfigFactory(
            product=product,
            zendesk_config=ZendeskConfigFactory(),
            is_active=True,
            subscription_only=True,
            unsubscribed_redirect_product=None,
        )
        data = self._search_json(product_slug="test-sub")
        self.assertIsNone(data["support_aaq_url"])

    def test_no_support_config_no_support_url(self):
        ProductFactory(slug="test-noconfig", visible=True)
        data = self._search_json(product_slug="test-noconfig")
        self.assertIsNone(data["support_aaq_url"])

    @override_settings(READ_ONLY=True)
    def test_read_only_mode_no_support_url(self):
        data = self._search_json()
        self.assertIsNone(data["support_aaq_url"])


class TestHybridSearchSwitch(TestCase):
    @override_switch("retrieval-hybrid-search", active=False)
    def test_disabled_switch_does_not_enter_retrieval(self):
        url = reverse("search", locale="en-US")
        with (
            mock.patch("kitsune.search.views.run_hybrid_search") as hybrid,
            mock.patch("kitsune.search.views.paginate", return_value=object()),
            mock.patch("kitsune.search.views._fallback_results", return_value=[]),
        ):
            response = self.client.get(f"{url}?q=firefox")

        self.assertEqual(response.status_code, 200)
        hybrid.assert_not_called()

    @override_switch("retrieval-hybrid-search", active=True)
    def test_enabled_switch_maps_all_three_source_tabs(self):
        url = reverse("search", locale="en-US")
        cases = ((1, {"kb"}), (2, {"aaq"}), (3, {"kb", "aaq"}))
        with mock.patch(
            "kitsune.search.views.run_hybrid_search", return_value=HYBRID_RESULT
        ) as hybrid:
            for where, expected in cases:
                with self.subTest(where=where):
                    response = self.client.get(f"{url}?format=json&q=firefox&w={where}")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(hybrid.call_args.kwargs["sources"], expected)
                    hybrid.reset_mock()

    @override_switch("retrieval-hybrid-search", active=True)
    def test_html_uses_approximate_count_and_previous_next(self):
        result = replace(
            HYBRID_RESULT,
            results=({**HYBRID_DOCUMENT, "search_summary": "<strong>Matched</strong> summary"},),
            approximate_total=23,
            page=2,
            has_previous=True,
            has_next=True,
        )
        url = reverse("search", locale="en-US")
        with mock.patch("kitsune.search.views.run_hybrid_search", return_value=result):
            response = self.client.get(f"{url}?q=firefox&page=2")

        doc = pq(response.content)
        self.assertIn("About 23 results", doc(".sumo-page-intro").text())
        self.assertEqual(doc(".pagination a").length, 2)
        self.assertIn("page=1", doc(".pagination .prev a").attr("href"))
        self.assertIn("page=3", doc(".pagination .next a").attr("href"))
        self.assertEqual(doc(".topic-article--text p strong").text(), "Matched")

        event = json.loads(doc(".topic-article a.title").attr("data-event-parameters"))
        self.assertEqual(event["search_result_source"], "kb")
        self.assertEqual(event["search_result_rank"], 11)
        self.assertNotIn("score", event)

    @override_settings(RETRIEVAL_MAX_PAGE_OFFSET=20)
    @override_switch("retrieval-hybrid-search", active=True)
    def test_json_clamps_page_and_does_not_invent_page_totals(self):
        result = replace(
            HYBRID_RESULT,
            approximate_total=23,
            page=3,
            has_previous=True,
            has_next=True,
        )
        url = reverse("search", locale="en-US")
        with mock.patch("kitsune.search.views.run_hybrid_search", return_value=result) as hybrid:
            response = self.client.get(f"{url}?format=json&q=firefox&page=99")

        data = json.loads(response.content)
        self.assertEqual(hybrid.call_args.kwargs["page"], 3)
        self.assertTrue(data["total_is_approximate"])
        self.assertEqual(
            data["pagination"],
            {"number": 3, "has_next": False, "has_previous": True},
        )

    @override_switch("retrieval-hybrid-search", active=True)
    def test_empty_first_page_does_not_show_a_positive_approximation(self):
        result = replace(HYBRID_RESULT, results=(), approximate_total=23, has_next=True)
        url = reverse("search", locale="en-US")
        with (
            mock.patch("kitsune.search.views.run_hybrid_search", return_value=result),
            mock.patch("kitsune.search.views._fallback_results", return_value=[]),
        ):
            response = self.client.get(f"{url}?q=firefox")

        doc = pq(response.content)
        text = doc(".sumo-page-intro").text()
        self.assertIn("0 results", text)
        self.assertNotIn("23", text)
        self.assertFalse(doc(".pagination"))

    @override_switch("retrieval-hybrid-search", active=True)
    def test_empty_later_page_redirects_to_the_first_page(self):
        result = replace(HYBRID_RESULT, results=(), page=2, has_previous=True)
        url = reverse("search", locale="en-US")
        with mock.patch("kitsune.search.views.run_hybrid_search", return_value=result):
            response = self.client.get(f"{url}?format=json&q=firefox&w=1&page=2")

        self.assertEqual(response.status_code, 302)
        self.assertIn("format=json", response.url)
        self.assertIn("q=firefox", response.url)
        self.assertIn("w=1", response.url)
        self.assertIn("page=1", response.url)
