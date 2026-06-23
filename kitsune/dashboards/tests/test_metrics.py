from datetime import date, timedelta
from unittest import mock

from django.core.cache import cache

from kitsune.dashboards.metrics import warm_wiki_metrics_cache
from kitsune.dashboards.models import (
    L10N_ACTIVE_CONTRIBUTORS_CODE,
    L10N_TOP20_CODE,
)
from kitsune.dashboards.tests import WikiMetricFactory
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse


class MetricsPageTests(TestCase):
    """The dashboard pages render for anonymous users (they are public)."""

    @mock.patch(
        "kitsune.dashboards.views.get_locales_by_visit", return_value=[("es", 1), ("fr", 2)]
    )
    def test_aggregated_page_renders(self, mocked_locales):
        response = self.client.get(reverse("dashboards.aggregated_metrics"))
        self.assertEqual(response.status_code, 200)

    def test_locale_page_renders(self):
        response = self.client.get(reverse("dashboards.locale_metrics", args=["es"]))
        self.assertEqual(response.status_code, 200)


class MetricsDataTests(TestCase):
    """Shape, one-year window, downsampling, and caching of the data endpoint."""

    def setUp(self):
        super().setUp()
        self.url = reverse("dashboards.wiki_metrics_data")

    def _payload(self, **params):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_grouped_by_code_then_locale(self):
        today = date.today()
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=today, value=50.0)
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="fr", date=today, value=60.0)

        data = self._payload()

        self.assertEqual(data[L10N_TOP20_CODE]["es"], [{"date": today.isoformat(), "value": 50.0}])
        self.assertEqual(data[L10N_TOP20_CODE]["fr"], [{"date": today.isoformat(), "value": 60.0}])

    def test_weekly_downsample_keeps_latest_in_week(self):
        # Two daily rows in the same ISO week collapse to the most recent.
        base = date.today() - timedelta(days=14)
        monday = base - timedelta(days=base.weekday())
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=monday, value=10.0)
        WikiMetricFactory(
            code=L10N_TOP20_CODE, locale="es", date=monday + timedelta(days=3), value=20.0
        )

        series = self._payload()[L10N_TOP20_CODE]["es"]

        self.assertEqual(
            series, [{"date": (monday + timedelta(days=3)).isoformat(), "value": 20.0}]
        )

    def test_duplicate_same_date_keeps_latest_row(self):
        # Two rows sharing a (code, locale, date) — e.g. the daily cron running
        # twice — collapse to the most recently inserted (highest id) one.
        today = date.today()
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=today, value=10.0)
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=today, value=20.0)

        series = self._payload()[L10N_TOP20_CODE]["es"]

        self.assertEqual(series, [{"date": today.isoformat(), "value": 20.0}])

    def test_excludes_rows_older_than_a_year(self):
        WikiMetricFactory(
            code=L10N_TOP20_CODE, locale="es", date=date.today() - timedelta(days=30), value=1.0
        )
        WikiMetricFactory(
            code=L10N_TOP20_CODE, locale="es", date=date.today() - timedelta(days=400), value=2.0
        )

        # Only the row within the fixed one-year window is returned.
        self.assertEqual([p["value"] for p in self._payload()[L10N_TOP20_CODE]["es"]], [1.0])

    def test_locale_filter_limits_payload(self):
        today = date.today()
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=today, value=1.0)
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="fr", date=today, value=2.0)

        data = self._payload(locale="es")

        self.assertEqual(list(data[L10N_TOP20_CODE].keys()), ["es"])

    def test_unknown_locale_404(self):
        response = self.client.get(self.url, {"locale": "zz"})
        self.assertEqual(response.status_code, 404)

    def test_product_bucket_isolation(self):
        today = date.today()
        product = ProductFactory()
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=today, value=1.0, product=None)
        WikiMetricFactory(
            code=L10N_TOP20_CODE, locale="es", date=today, value=2.0, product=product
        )

        # No product param => the "All products" (null) bucket only.
        self.assertEqual([p["value"] for p in self._payload()[L10N_TOP20_CODE]["es"]], [1.0])
        # A product slug => that product's bucket only.
        self.assertEqual(
            [p["value"] for p in self._payload(product=product.slug)[L10N_TOP20_CODE]["es"]],
            [2.0],
        )

    def test_monthly_contributors_pass_through(self):
        first_of_month = date.today().replace(day=1)
        WikiMetricFactory(
            code=L10N_ACTIVE_CONTRIBUTORS_CODE, locale="es", date=first_of_month, value=7.0
        )

        data = self._payload()

        self.assertEqual(
            data[L10N_ACTIVE_CONTRIBUTORS_CODE]["es"],
            [{"date": first_of_month.isoformat(), "value": 7.0}],
        )

    def test_response_is_cached_until_expiry(self):
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=date.today(), value=1.0)
        self.assertIn("es", self._payload()[L10N_TOP20_CODE])

        # A new row is not reflected while the cached payload is still valid.
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="fr", date=date.today(), value=2.0)
        self.assertNotIn("fr", self._payload()[L10N_TOP20_CODE])

        # Simulate the payload's TTL expiring by dropping its cache entry (the
        # default request maps to the all-products/all-locales key); the next
        # request then rebuilds it from the current data.
        cache.delete("wikimetrics:agg:all:all")
        self.assertIn("fr", self._payload()[L10N_TOP20_CODE])

    def test_warm_cache_refreshes_aggregated_payload(self):
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=date.today(), value=1.0)
        self.assertIn("es", self._payload()[L10N_TOP20_CODE])

        # A new row isn't visible while the cached payload is still valid...
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="fr", date=date.today(), value=2.0)
        self.assertNotIn("fr", self._payload()[L10N_TOP20_CODE])

        # ...but warming (what the cron tasks do after refreshing the data)
        # overwrites the cached all-locales payload in place, no eviction needed.
        warm_wiki_metrics_cache()
        self.assertIn("fr", self._payload()[L10N_TOP20_CODE])
