import logging

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render
from django.utils.datastructures import SortedDict

from apiclient.errors import Error as GoogleAPIError
from oauth2client.client import Error as Oauth2Error
from OpenSSL.crypto import Error as OpenSSLError

from kitsune.announcements.models import Announcement
from kitsune.announcements.forms import AnnouncementForm
from kitsune.lib.sumo_locales import LOCALES
from kitsune.products.models import Product
from kitsune.sumo.googleanalytics import visitors_by_locale
from kitsune.wiki.events import (
    ApproveRevisionInLocaleEvent, ReadyRevisionEvent,
    ReviewableRevisionInLocaleEvent)


log = logging.getLogger('k.dashboards')


def render_readouts(request, readouts, template, locale=None, extra_data=None,
                    product=None):
    """Render a readouts, possibly with overview page.

    Use the given template, pass the template the given readouts, limit the
    considered data to the given locale, and pass along anything in the
    `extra_data` dict to the template in addition to the standard data.

    """
    current_locale = locale or request.LANGUAGE_CODE
    on_default_locale = request.LANGUAGE_CODE == settings.WIKI_DEFAULT_LANGUAGE
    data = {'readouts': SortedDict((slug, class_(request, locale=locale,
                                                 product=product))
                                   for slug, class_ in readouts.iteritems()
                                   if class_.should_show_to(request)),
            'default_locale': settings.WIKI_DEFAULT_LANGUAGE,
            'default_locale_name':
                LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
            'current_locale': current_locale,
            'current_locale_name': LOCALES[current_locale].native,
            'request_locale_name': LOCALES[request.LANGUAGE_CODE].native,
            'is_watching_default_approved':
                ApproveRevisionInLocaleEvent.is_notifying(
                    request.user, locale=settings.WIKI_DEFAULT_LANGUAGE),
            'is_watching_other_approved':
                None if on_default_locale
                else ApproveRevisionInLocaleEvent.is_notifying(
                    request.user, locale=request.LANGUAGE_CODE),
            'is_watching_default_locale':
                ReviewableRevisionInLocaleEvent.is_notifying(
                    request.user, locale=settings.WIKI_DEFAULT_LANGUAGE),
            'is_watching_other_locale':
                None if on_default_locale
                else ReviewableRevisionInLocaleEvent.is_notifying(
                    request.user, locale=request.LANGUAGE_CODE),
            'is_watching_default_ready':
                ReadyRevisionEvent.is_notifying(request.user),
            'on_default_locale': on_default_locale,
            'announce_form': AnnouncementForm(),
            'announcements': Announcement.get_for_locale_name(current_locale),
            'product': product,
            'products': Product.objects.filter(visible=True),
        }
    if extra_data:
        data.update(extra_data)
    return render(request, 'dashboards/' + template, data)


# Cache it all day to avoid calling Google Analytics over and over.
CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours


def get_locales_by_visit(start_date, end_date):
    """Get a list of (locale, visits) tuples sorted descending by visits."""

    cache_key = 'locales_sorted_by_visits:{start}:{end}'.format(
        start=start_date, end=end_date)

    sorted_locales = cache.get(cache_key)
    if sorted_locales is None:
        try:
            results = visitors_by_locale(start_date, end_date)
            locales_and_visits = results.items()
            sorted_locales = list(reversed(sorted(
                locales_and_visits, key=lambda x: x[1])))
            cache.add(cache_key, sorted_locales, CACHE_TIMEOUT)
        except (GoogleAPIError, Oauth2Error, OpenSSLError):
            # Just return all locales with 0s for visits.
            log.exception('Something went wrong getting visitors by locale '
                          'from Google Analytics. Nobody got a 500 though.')
            sorted_locales = [(l, 0) for l in settings.SUMO_LANGUAGES]

    return sorted_locales
