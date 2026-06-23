from datetime import date, timedelta

from django.core.cache import cache
from django.db.models.functions import TruncWeek

from kitsune.dashboards.models import WikiMetric
from kitsune.products.models import Product

# The metrics dashboards always show a fixed one-year window.
WINDOW_DAYS = 365

# The coverage cron re-warms these payloads once a day. Keep the TTL comfortably
# longer than that 24-hour interval so a successful warm always overwrites a
# still-live entry; if the TTL matched the interval, expiry would race the next
# warm and leave a cold gap (forcing an on-request rebuild) on roughly half the
# days. The extra two hours absorb cron jitter and Celery queue latency. The
# cache only goes cold when a warm is actually missed.
WIKI_METRICS_CACHE_TIMEOUT = 26 * 60 * 60  # 26 hours


def _build_payload(product, locale):
    """Build the shaped metrics payload from the database.

    The daily coverage codes are downsampled to one point per ISO week (the
    most recent row in each week); the monthly active-contributors code already
    has at most one row per month, so it passes through unchanged.

    Returns {code: {locale: [{"date": iso, "value": float}, ...ascending]}}.
    """
    cutoff = date.today() - timedelta(days=WINDOW_DAYS)

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


def _cache_key(product, locale):
    product_key = product.slug if product else "all"
    locale_key = locale or "all"
    return f"wikimetrics:agg:{product_key}:{locale_key}"


def get_wiki_metrics_data(product, locale=None):
    """Return the cached metrics payload for the given product/locale.

    `product` is a Product instance or None (the "All products" bucket).
    `locale` limits the payload to a single locale (used by the per-locale
    dashboard). The payload always covers a fixed one-year window.

    Cached for WIKI_METRICS_CACHE_TIMEOUT. The data-refresh cron tasks call
    warm_wiki_metrics_cache() to recompute and reset this entry, so in normal
    operation the TTL is just a backstop for a missed cron run.
    """
    return cache.get_or_set(
        _cache_key(product, locale),
        lambda: _build_payload(product, locale),
        WIKI_METRICS_CACHE_TIMEOUT,
    )


def warm_wiki_metrics_cache():
    """Recompute and cache the aggregated (all-locales) payloads.

    Called by the cron tasks after the WikiMetric rows are refreshed. Using
    cache.set (not get_or_set) overwrites the existing entries and resets their
    TTL, so the expensive all-locales query is never run on a user request and
    there's no cold-cache stampede. The per-locale payloads are cheap and left
    to populate on demand.
    """
    for product in [None, *Product.objects.filter(visible=True)]:
        cache.set(
            _cache_key(product, None),
            _build_payload(product, None),
            WIKI_METRICS_CACHE_TIMEOUT,
        )
