import contextlib
import re
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import BACKEND_SESSION_KEY, logout
from django.core.exceptions import MiddlewareNotUsed
from django.core.urlresolvers import is_valid_path
from django.core.validators import ValidationError, validate_ipv4_address
from django.db.utils import DatabaseError
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponsePermanentRedirect, HttpResponseRedirect)
from django.http.request import split_domain_port
from django.shortcuts import render
from django.utils import translation
from django.utils.cache import (add_never_cache_headers,
                                patch_response_headers, patch_vary_headers)
from django.utils.encoding import iri_to_uri, smart_bytes, smart_text
from enforce_host import EnforceHostMiddleware
from mozilla_django_oidc.middleware import SessionRefresh

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
            query = dict((smart_bytes(k), v) for
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
                                  smart_text(request.META['QUERY_STRING']))
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


class InAAQMiddleware(MiddlewareMixin):
    """
    Middleware that updates session's keys based on the view used.

    aaq_* views -> in-aaq = True
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        # This key is used both in templates and the
        # LogoutDeactivateUsersMiddleware

        if not request.session or not callback:
            return None
        try:
            view_name = callback.func_name
        except AttributeError:
            return None

        # If we are authenticating or there is no session, do nothing
        if view_name in ['user_auth', 'login', 'serve_cors']:
            return None
        if 'aaq' in view_name:
            request.session['in-aaq'] = True
            request.session['product_key'] = callback_kwargs.get('product_key')
        else:
            request.session['in-aaq'] = False
            if '/questions/new' not in request.META.get('HTTP_REFERER', ''):
                request.session['product_key'] = ''
        return None
