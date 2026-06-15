from datetime import date, timedelta
from unittest import mock

from django.conf import settings
from django.core.cache import cache

from kitsune.dashboards.decorators import can_view_l10n_metrics
from kitsune.dashboards.models import (
    L10N_ACTIVE_CONTRIBUTORS_CODE,
    L10N_TOP20_CODE,
)
from kitsune.dashboards.tests import WikiMetricFactory
from kitsune.products.tests import ProductFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import GroupFactory, UserFactory
from kitsune.wiki.tests import LocaleFactory


class MetricsAccessTests(TestCase):
    """Access control for the wiki-metrics data endpoint."""

    def setUp(self):
        super().setUp()
        self.url = reverse("dashboards.wiki_metrics_data")

    def _status(self, user=None):
        if user:
            self.client.force_login(user)
        return self.client.get(self.url).status_code

    def test_anonymous_denied(self):
        self.assertEqual(self._status(), 404)

    def test_authenticated_non_member_denied(self):
        self.assertEqual(self._status(UserFactory()), 404)

    def test_l10n_contributor_group_allowed(self):
        user = UserFactory(groups=[GroupFactory(name="l10n-contributors")])
        self.assertEqual(self._status(user), 200)

    def test_staff_group_allowed(self):
        user = UserFactory(groups=[GroupFactory(name=settings.STAFF_GROUP)])
        self.assertEqual(self._status(user), 200)

    def test_unrelated_group_denied(self):
        user = UserFactory(groups=[GroupFactory(name="Some Other Group")])
        self.assertEqual(self._status(user), 404)

    def test_inactive_member_denied(self):
        # Inactive users never reach the view (LogoutDeactivatedUsersMiddleware
        # redirects them first), so verify the gate's is_active branch directly.
        active = UserFactory(groups=[GroupFactory(name="l10n-contributors")])
        inactive = UserFactory(groups=[GroupFactory(name="l10n-contributors")], is_active=False)
        self.assertTrue(can_view_l10n_metrics(active))
        self.assertFalse(can_view_l10n_metrics(inactive))

    def test_locale_leader_allowed(self):
        user = UserFactory()
        LocaleFactory(locale="es").leaders.add(user)
        self.assertEqual(self._status(user), 200)

    def test_locale_reviewer_allowed(self):
        user = UserFactory()
        LocaleFactory(locale="fr").reviewers.add(user)
        self.assertEqual(self._status(user), 200)

    def test_locale_editor_allowed(self):
        user = UserFactory()
        LocaleFactory(locale="de").editors.add(user)
        self.assertEqual(self._status(user), 200)


class MetricsPageAccessTests(TestCase):
    """Access control for the two dashboard page views."""

    def setUp(self):
        super().setUp()
        self.member = UserFactory(groups=[GroupFactory(name="l10n-contributors")])

    @mock.patch(
        "kitsune.dashboards.views.get_locales_by_visit", return_value=[("es", 1), ("fr", 2)]
    )
    def test_aggregated_page_gated(self, mocked_locales):
        url = reverse("dashboards.aggregated_metrics")
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_locale_page_gated(self):
        url = reverse("dashboards.locale_metrics", args=["es"])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(url).status_code, 200)


class MetricsDataTests(TestCase):
    """Shape, windowing, downsampling, and caching of the data endpoint."""

    def setUp(self):
        super().setUp()
        self.client.force_login(UserFactory(groups=[GroupFactory(name="l10n-contributors")]))
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

    def test_window_excludes_older_rows(self):
        WikiMetricFactory(
            code=L10N_TOP20_CODE, locale="es", date=date.today() - timedelta(days=10), value=1.0
        )
        WikiMetricFactory(
            code=L10N_TOP20_CODE, locale="es", date=date.today() - timedelta(days=200), value=2.0
        )

        # 3-month window drops the 200-day-old row.
        self.assertEqual(
            [p["value"] for p in self._payload(window="3m")[L10N_TOP20_CODE]["es"]], [1.0]
        )
        # 12-month window keeps both (in two distinct weeks).
        self.assertEqual(
            sorted(p["value"] for p in self._payload(window="12m")[L10N_TOP20_CODE]["es"]),
            [1.0, 2.0],
        )

    def test_invalid_window_falls_back_to_default(self):
        WikiMetricFactory(code=L10N_TOP20_CODE, locale="es", date=date.today(), value=5.0)
        response = self.client.get(self.url, {"window": "bogus"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(L10N_TOP20_CODE, response.json())

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

        # Simulate the payload's TTL expiring by dropping just its cache entry
        # (the default request maps to the all-products/3m/all-locales key); the
        # next request then rebuilds it from the current data.
        cache.delete("wikimetrics:agg:all:3m:all")
        self.assertIn("fr", self._payload()[L10N_TOP20_CODE])
