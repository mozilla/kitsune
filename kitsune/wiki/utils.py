import random

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.http import urlencode

from kitsune.dashboards import LAST_7_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.wiki.models import Document, Revision


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


def get_featured_articles(product=None, locale=settings.WIKI_DEFAULT_LANGUAGE):
    """Returns 4 random articles from the most visited.

    If a product is passed, it returns 4 random highly visited articles.
    """
    visits = (
        WikiDocumentVisits.objects.filter(period=LAST_7_DAYS)
        .exclude(document__products__slug__in=settings.EXCLUDE_PRODUCT_SLUGS_FEATURED_ARTICLES)
        .order_by("-visits")
        .select_related("document")
    )

    if product:
        visits = visits.filter(document__products__in=[product.id])

    visits = visits[:10]
    documents = []

    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        for visit in visits:
            documents.append(visit.document)
    else:
        # prefretch localised documents to avoid n+1 problem
        visits = visits.prefetch_related(
            Prefetch(
                "document__translations",
                queryset=Document.objects.filter(
                    locale=locale, current_revision__is_approved=True
                ),
            )
        )

        for visit in visits:
            translation = visit.document.translations.first()
            if not translation:
                continue
            documents.append(translation)

    if len(documents) <= 4:
        return documents
    return random.sample(documents, 4)


def get_visible_document_or_404(user, **kwargs):
    """
    Get the document specified by the keyword arguments and visible to the given user, or 404.
    """

    look_for_translation_via_parent = kwargs.pop("look_for_translation_via_parent", False)
    return_parent_if_no_translation = kwargs.pop("return_parent_if_no_translation", False)

    try:
        return Document.objects.get_visible(user, **kwargs)
    except Document.DoesNotExist:
        pass

    if (
        not look_for_translation_via_parent
        or not (locale := kwargs.get("locale"))
        or (locale == settings.WIKI_DEFAULT_LANGUAGE)
    ):
        # We either don't want to try to find the translation via its parent, or it doesn't
        # make sense, because we're not making a locale-specific request or the locale we're
        # requesting is already the default locale.
        raise Http404

    # We couldn't find a visible translation in the requested non-default locale, so let's
    # see if we can find a visible translation via its parent.
    kwargs.update(locale=settings.WIKI_DEFAULT_LANGUAGE)
    parent = get_object_or_404(Document.objects.visible(user, **kwargs))

    # If there's a visible translation of the parent for the requested locale, return it.
    if translation := parent.translated_to(locale, visible_for_user=user):
        return translation

    # Otherwise, we're left with the parent.
    if return_parent_if_no_translation:
        return parent

    raise Http404


def get_visible_revision_or_404(user, **kwargs):
    return get_object_or_404(Revision.objects.visible(user, **kwargs))
