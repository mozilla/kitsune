import random
import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.http import urlencode

from kitsune.dashboards import LAST_7_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.wiki.models import Revision


class BitlyException(Exception):
    """Bitly Exception for any other errors."""

    pass


class BitlyUnauthorizedException(BitlyException):
    """Bitly Exception for an unauthorized error."""

    pass


class BitlyRateLimitException(BitlyException):
    """Bitly Exception for a rate limiting error."""

    pass


def active_contributors(from_date, to_date=None, locale=None, product=None):
    """Return active KB contributors for the specified parameters.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    return User.objects.filter(
        id__in=_active_contributors_id(from_date, to_date, locale, product)
    ).order_by("username")


def generate_short_url(long_url):
    """Return a shortned URL for a given long_url via bitly's API.

    :arg long_url: URL to shorten
    """

    # Check for empty credentials.
    if settings.BITLY_LOGIN is None or settings.BITLY_API_KEY is None:
        return ""

    keys = {
        "format": "json",
        "longUrl": long_url,
        "login": settings.BITLY_LOGIN,
        "apiKey": settings.BITLY_API_KEY,
    }
    params = urlencode(keys)

    resp = requests.post(settings.BITLY_API_URL, params).json()
    if resp["status_code"] == 200:
        short_url = resp.get("data", {}).get("url", "")
        return short_url
    elif resp["status_code"] == 401:
        raise BitlyUnauthorizedException("Unauthorized access to bitly's API")
    elif resp["status_code"] == 403:
        raise BitlyRateLimitException("Rate limit exceeded while using " "bitly's API.")
    else:
        raise BitlyException(
            "Error code: {0} recieved from bitly's API.".format(resp["status_code"])
        )


def num_active_contributors(from_date, to_date=None, locale=None, product=None):
    """Return number of active KB contributors for the specified parameters.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    return len(_active_contributors_id(from_date, to_date, locale, product))


def _active_contributors_id(from_date, to_date, locale, product):
    """Return the set of ids for the top contributors based on the params.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    editors = (
        Revision.objects.filter(created__gte=from_date)
        .values_list("creator", flat=True)
        .distinct()
    )

    reviewers = (
        Revision.objects.filter(reviewed__gte=from_date)
        .values_list("reviewer", flat=True)
        .distinct()
    )

    if to_date:
        editors = editors.filter(created__lt=to_date)
        reviewers = reviewers.filter(reviewed__lt=to_date)

    if locale:
        editors = editors.filter(document__locale=locale)
        reviewers = reviewers.filter(document__locale=locale)

    if product:
        editors = editors.filter(
            Q(document__products=product) | Q(document__parent__products=product)
        )
        reviewers = reviewers.filter(
            Q(document__products=product) | Q(document__parent__products=product)
        )

    return set(list(editors) + list(reviewers))


def get_featured_articles(product=None):
    """Returns 4 random articles from the most visited.

    If a product is passed, it returns 4 random highly visited articles.
    """
    featured = (
        WikiDocumentVisits.objects.filter(period=LAST_7_DAYS)
        .exclude(
            document__products__slug__in=settings.EXCLUDE_PRODUCT_SLUGS_FEATURED_ARTICLES
        )
        .order_by("-visits")
        .select_related("document")
    )

    if product:
        featured = featured.filter(document__products__in=[product.id])

    # Limit this to 10 entries
    if featured.count() < 10:
        return featured

    # This returns a WikiDocumentVisits object and not the actual Wiki doc.
    # The wiki doc it's under .document which is prefetched b/c of select_related
    featured = featured[:10]
    return random.sample(featured, 4)
