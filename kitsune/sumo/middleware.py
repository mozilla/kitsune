import contextlib
import re
import urllib.request, urllib.parse, urllib.error

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import BACKEND_SESSION_KEY, logout
from django.core.exceptions import MiddlewareNotUsed
from django.core.urlresolvers import is_valid_path
from django.core.validators import validate_ipv4_address, ValidationError
from django.db.utils import DatabaseError
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponsePermanentRedirect, HttpResponseForbidden)
from django.http.request import split_domain_port
from django.shortcuts import render
from django.utils import translation
from django.utils.cache import add_never_cache_headers, patch_response_headers, patch_vary_headers
from django.utils.encoding import iri_to_uri, smart_str, smart_unicode

import mobility
from mozilla_django_oidc.middleware import SessionRefresh
from enforce_host import EnforceHostMiddleware

from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import Prefixer, set_url_prefixer, split_path
from kitsune.sumo.views import handle403


try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


class EnforceHostIPMiddleware(EnforceHostMiddleware):
    """Modify the `EnforceHostMiddleware` to allow IP addresses"""
    def process_request(self, request):
        host = request.get_host()
        domain, port = split_domain_port(host)
        try:
            validate_ipv4_address(domain)
        except ValidationError:
            # not an IP address. Call the superclass
            return super(EnforceHostIPMiddleware, self).process_request(request)

        # it is an IP address
        return


class HttpResponseRateLimited(HttpResponse):
    status_code = 429


class SUMORefreshIDTokenAdminMiddleware(SessionRefresh):
    def __init__(self, *args, **kwargs):
        if not settings.OIDC_ENABLE or settings.DEV:
            raise MiddlewareNotUsed

    def process_request(self, request):
        """Only allow refresh and enforce OIDC auth on admin URLs"""
        # If the admin is targeted let's check the backend used, if any
        if request.path.startswith('/admin/') and request.path != '/admin/login/':
            backend = request.session.get(BACKEND_SESSION_KEY)
            if backend and backend.split('.')[-1] != 'SumoOIDCAuthBackend':
                logout(request)
                messages.error(request, 'OIDC login required for admin access')
                return HttpResponseRedirect('/admin/login/')

            return super(SUMORefreshIDTokenAdminMiddleware, self).process_request(request)


class LocaleURLMiddleware(object):
    """
    Based on zamboni.amo.middleware.
    Tried to use localeurl but it choked on 'en-US' with capital letters.

    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def process_request(self, request):
        prefixer = Prefixer(request)
        set_url_prefixer(prefixer)
        full_path = prefixer.fix(prefixer.shortened_path)

        if request.GET.get('lang', '') in settings.SUMO_LANGUAGES:
            # Blank out the locale so that we can set a new one. Remove lang
            # from the query params so we don't have an infinite loop.

            prefixer.locale = ''
            new_path = prefixer.fix(prefixer.shortened_path)
            query = dict((smart_str(k), v) for
                         k, v in request.GET.items() if k != 'lang')

            # 'lang' is only used on the language selection page. If this is
            # present it is safe to set language preference for the current
            # user.
            if request.user.is_anonymous():
                cookie = settings.LANGUAGE_COOKIE_NAME
                request.session[cookie] = request.GET['lang']

            return HttpResponseRedirect(urlparams(new_path, **query))

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.parse.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponseRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, _ = split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.LANGUAGE_CODE = prefixer.locale
        translation.activate(prefixer.locale)

    def process_response(self, request, response):
        """Unset the thread-local var we set during `process_request`."""
        # This makes mistaken tests (that should use LocalizingClient but
        # use Client instead) fail loudly and reliably. Otherwise, the set
        # prefixer bleeds from one test to the next, making tests
        # order-dependent and causing hard-to-track failures.
        set_url_prefixer(None)
        return response

    def process_exception(self, request, exception):
        set_url_prefixer(None)


class Forbidden403Middleware(object):
    """
    Renders a 403.html page if response.status_code == 403.
    """
    def process_response(self, request, response):
        if isinstance(response, HttpResponseForbidden):
            return handle403(request)
        # If not 403, return response unmodified
        return response


class VaryNoCacheMiddleware(MiddlewareMixin):
    """
    If enabled this will set headers to prevent the CDN (or other caches) from
    caching the response if the response was set to vary on accept-langauge.
    This should be near the top of the list of middlewares so it will be able
    to inspect the near-final response since response middleware is processed
    in reverse.
    """
    def __init__(self):
        if not settings.ENABLE_VARY_NOCACHE_MIDDLEWARE:
            raise MiddlewareNotUsed

    @staticmethod
    def process_response(request, response):
        if 'vary' in response and 'accept-language' in response['vary'].lower():
            add_never_cache_headers(response)

        return response


class CacheHeadersMiddleware(MiddlewareMixin):
    """
    Sets no-cache headers normally, and cache for some time in READ_ONLY mode.
    """
    def process_response(self, request, response):
        if 'cache-control' in response or response.status_code >= 400:
            return response

        if (request.method in ('GET', 'HEAD') and
                settings.CACHE_MIDDLEWARE_SECONDS):
            # uses CACHE_MIDDLEWARE_SECONDS by default
            patch_response_headers(response)
        else:
            add_never_cache_headers(response)

        return response


class PlusToSpaceMiddleware(object):
    """Replace old-style + with %20 in URLs."""
    def process_request(self, request):
        p = re.compile(r'\+')
        if p.search(request.path_info):
            new = p.sub(' ', request.path_info)
            if request.META.get('QUERY_STRING'):
                new = '%s?%s' % (new,
                                  smart_unicode(request.META['QUERY_STRING']))
            if hasattr(request, 'LANGUAGE_CODE'):
                new = '/%s%s' % (request.LANGUAGE_CODE, new)
            return HttpResponsePermanentRedirect(new)


class ReadOnlyMiddleware(object):
    def __init__(self):
        if not settings.READ_ONLY:
            raise MiddlewareNotUsed

    def process_request(self, request):
        if request.method == 'POST':
            return render(request, 'sumo/read-only.html', status=503)

    def process_exception(self, request, exception):
        if isinstance(exception, DatabaseError):
            return render(request, 'sumo/read-only.html', status=503)


class RemoveSlashMiddleware(object):
    """
    Middleware that tries to remove a trailing slash if there was a 404.

    If the response is a 404 because url resolution failed, we'll look for a
    better url without a trailing slash.
    """

    def process_response(self, request, response):
        if (response.status_code == 404 and
                request.path_info.endswith('/') and
                not is_valid_path(request.path_info) and
                is_valid_path(request.path_info[:-1])):
            # Use request.path because we munged app/locale in path_info.
            newurl = request.path[:-1]
            if request.GET:
                with safe_query_string(request):
                    newurl += '?' + request.META['QUERY_STRING']
            return HttpResponsePermanentRedirect(newurl)
        return response


@contextlib.contextmanager
def safe_query_string(request):
    """
    Turn the QUERY_STRING into a unicode- and ascii-safe string.

    We need unicode so it can be combined with a reversed URL, but it has to be
    ascii to go in a Location header.  iri_to_uri seems like a good compromise.
    """
    qs = request.META['QUERY_STRING']
    try:
        request.META['QUERY_STRING'] = iri_to_uri(qs)
        yield
    finally:
        request.META['QUERY_STRING'] = qs


# Mobile user agents.
MOBILE_UAS = re.compile('android|fennec|mobile|iphone|opera (?:mini|mobi)')

# Tablet user agents. User agents matching tablets will not be considered
# to be mobile (for tablets, request.MOBILE = False).
TABLET_UAS = re.compile('tablet|ipad')


# This is a modified version of 'mobility.middleware.DetectMobileMiddleware'.
# We want to exclude tablets from being detected as MOBILE and there is
# no way to do that by just overriding the detection regex.
class DetectMobileMiddleware(MiddlewareMixin):
    """Looks at user agent and decides whether the device is mobile."""
    def __init__(self, *args, **kwargs):
        if settings.SKIP_MOBILE_DETECTION:
            raise MiddlewareNotUsed()

    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '').lower()
        mc = request.COOKIES.get(settings.MOBILE_COOKIE)
        is_tablet = TABLET_UAS.search(ua)
        is_mobile = not is_tablet and MOBILE_UAS.search(ua)
        if (is_mobile and mc != 'off') or mc == 'on':
            request.META['HTTP_X_MOBILE'] = '1'

    def process_response(self, request, response):
        patch_vary_headers(response, ['User-Agent'])
        return response


class MobileSwitchMiddleware(object):
    """Looks for query string parameters to switch to the mobile site."""
    def process_request(self, request):
        mobile = request.GET.get('mobile')

        if mobile == '0':
            request.MOBILE = False
        elif mobile == '1':
            request.MOBILE = True

    def process_response(self, request, response):
        mobile = request.GET.get('mobile')

        if mobile == '0':
            response.set_cookie(mobility.middleware.COOKIE, 'off')
        elif mobile == '1':
            response.set_cookie(mobility.middleware.COOKIE, 'on')

        return response


class HostnameMiddleware(MiddlewareMixin):
    def __init__(self):
        if getattr(settings, 'DISABLE_HOSTNAME_MIDDLEWARE', False):
            raise MiddlewareNotUsed()

        values = [getattr(settings, x) for x in ['PLATFORM_NAME', 'K8S_DOMAIN']]
        self.backend_server = '.'.join(x for x in values if x)

    def process_response(self, request, response):
        response['X-Backend-Server'] = self.backend_server
        return response


class FilterByUserAgentMiddleware(MiddlewareMixin):
    """Looks at user agent and decides whether the device is allowed on the site."""
    def __init__(self, *args, **kwargs):
        if not settings.USER_AGENT_FILTERS:
            raise MiddlewareNotUsed()

    def process_request(self, request):
        client_ua = request.META.get('HTTP_USER_AGENT', '').lower()
        # get only ascii chars
        ua = ''.join(i for i in client_ua if ord(i) < 128)

        if any(x in ua for x in settings.USER_AGENT_FILTERS):
            response = HttpResponseRateLimited()
            patch_vary_headers(response, ['User-Agent'])
            return response
