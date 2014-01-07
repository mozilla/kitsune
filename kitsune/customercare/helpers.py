from datetime import datetime

from django.conf import settings

import pytz
from jingo import register

from kitsune.sumo.helpers import timesince


@register.filter
def utctimesince(time, now=None):
    now = now or datetime.utcnow()
    return timesince(time, now)


def _append_tz(t):
    tz = pytz.timezone(settings.TIME_ZONE)
    return tz.localize(t)


@register.filter
def isotime(t):
    """Date/Time format according to ISO 8601"""
    if not hasattr(t, 'tzinfo'):
        return
    return _append_tz(t).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@register.filter
def round_percent(num):
    """Return a customercare-format percentage from a number."""
    return round(num, 1) if num < 10 else int(round(num, 0))


@register.filter
def max(num, limit):
    if num > limit:
        num = limit
    return num
