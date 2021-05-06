import json
import logging
import socket

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from kitsune.lib.sumo_locales import LOCALES
from kitsune.sumo.decorators import cors_enabled
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import get_next_url, uselocale

log = logging.getLogger("k.services")


@never_cache
def locales(request):
    """The locale switcher page."""
    template = "sumo/locales.html"

    return render(request, template, dict(next_url=get_next_url(request) or reverse("home")))


def geoip_suggestion(request):
    """
    Ajax view to return the localized text for GeoIP locale change suggestion.

    Takes one parameter from the querystring:

        * locales - a form encoded list of locales to translate to.

    Example url: /localize?locales[]=es&locales[]=en-US
    """
    locales = request.GET.getlist("locales[]")

    response = {"locales": {}}
    for locale in locales:
        # English and native names for the language
        response["locales"][locale] = LOCALES.get(locale, "")
        with uselocale(locale):
            # This is using our JS-style string formatting.
            response[locale] = {
                "suggestion": _("Would you like to view this page in " "%(language)s instead?"),
                "confirm": _("Yes"),
                "cancel": _("No"),
            }

    return HttpResponse(json.dumps(response), content_type="application/json")


def handle403(request):
    """A 403 message that looks nicer than the normal Apache forbidden page"""
    return render(request, "handlers/403.html", status=403)


def handle404(request, *args, **kwargs):
    """A handler for 404s"""
    return render(request, "handlers/404.html", status=404)


def handle500(request):
    """A 500 message that looks nicer than the normal Apache error page"""
    return render(request, "handlers/500.html", status=500)


def redirect_to(request, url, permanent=True, **kwargs):
    """Like Django's redirect_to except that 'url' is passed to reverse."""
    dest = reverse(url, kwargs=kwargs)
    if permanent:
        return HttpResponsePermanentRedirect(dest)

    return HttpResponseRedirect(dest)


def deprecated_redirect(request, url, **kwargs):
    """Redirect with an interstitial page telling folks to update their
    bookmarks.
    """
    dest = reverse(url, kwargs=kwargs)
    proto = "https://" if request.is_secure() else "http://"
    host = Site.objects.get_current().domain
    return render(request, "sumo/deprecated.html", {"dest": dest, "proto": proto, "host": host})


def robots(request):
    """Generate a robots.txt."""
    if not settings.ENGAGE_ROBOTS:
        template = "User-Agent: *\nDisallow: /"
    else:
        template = render(request, "sumo/robots.html")
    return HttpResponse(template, content_type="text/plain")


def test_memcached(host, port):
    """Connect to memcached.

    :returns: True if test passed, False if test failed.

    """
    try:
        s = socket.socket()
        s.connect((host, port))
        return True
    except Exception as exc:
        log.critical("Failed to connect to memcached (%r): %s" % ((host, port), exc))
        return False
    finally:
        s.close()


@cors_enabled("*")
def serve_cors(*args, **kwargs):
    """A wrapper around django.views.static.serve that adds CORS headers."""
    if not settings.DEBUG:
        raise RuntimeError("Don't use kitsune.sumo.views.serve_cors " "in production.")
    from django.views.static import serve

    return serve(*args, **kwargs)
