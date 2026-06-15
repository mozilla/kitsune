from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.cache import cache
from django.db.models.functions import TruncWeek

from kitsune.dashboards.models import WikiMetric

# Selectable windows for the aggregated metrics dashboard, in months.
WINDOW_CHOICES = {"3m": 3, "6m": 6, "9m": 9, "12m": 12}
DEFAULT_WINDOW = "3m"


def _build_payload(product, window_months, locale):
    """Build the shaped metrics payload from the database.

    The daily coverage codes are downsampled to one point per ISO week (the
    most recent row in each week); the monthly active-contributors code already
    has at most one row per month, so it passes through unchanged.

    Returns {code: {locale: [{"date": iso, "value": float}, ...ascending]}}.
    """
    cutoff = date.today() - relativedelta(months=window_months)

    queryset = WikiMetric.objects.filter(date__gte=cutoff, product=product)
    if locale:
        queryset = queryset.filter(locale=locale)

    # We keep one row per (code, locale, week). Weeks are returned
    # ascending, so each series is already in ascending-date order.
    rows = (
        queryset.annotate(week=TruncWeek("date"))
        .order_by("code", "locale", "week", "-date", "-id")
        .distinct("code", "locale", "week")
        .values("code", "locale", "date", "value", "week")
    )

    payload = {}
    for row in rows:
        by_locale = payload.setdefault(row["code"], {})
        by_locale.setdefault(row["locale"] or "", []).append(
            {"date": row["date"].isoformat(), "value": row["value"]}
        )

    return payload


def get_wiki_metrics_data(product, window, locale=None):
    """Return the cached metrics payload for the given product/window/locale.

    `window` must be a key of WINDOW_CHOICES. `product` is a Product instance or
    None (the "All products" bucket). `locale` limits the payload to a single
    locale (used by the per-locale dashboard).

    Cached for CACHE_LONG_TIMEOUT (24 hours), which matches the daily cadence of
    the cron task that refreshes the underlying WikiMetric rows, so the cache
    turns over about as often as the data does.
    """
    product_key = product.slug if product else "all"
    locale_key = locale or "all"
    cache_key = f"wikimetrics:agg:{product_key}:{window}:{locale_key}"

    return cache.get_or_set(
        cache_key,
        lambda: _build_payload(product, WINDOW_CHOICES[window], locale),
        settings.CACHE_LONG_TIMEOUT,
    )
