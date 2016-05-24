import contextlib
import re
import urllib

from django.conf import settings
from django.core.urlresolvers import is_valid_path
from django.db.utils import DatabaseError
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.utils.encoding import iri_to_uri, smart_str, smart_unicode

import mobility

from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import Prefixer, set_url_prefixer, split_path
from kitsune.sumo.views import handle403


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
                         k, v in request.GET.iteritems() if k != 'lang')

            # 'lang' is only used on the language selection page. If this is
            # present it is safe to set language preference for the current
            # user.
            if request.user.is_anonymous():
                cookie = settings.LANGUAGE_COOKIE_NAME
                request.session[cookie] = request.GET['lang']

            return HttpResponseRedirect(urlparams(new_path, **query))

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.quote(full_path.encode('utf-8'))

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


class NoCacheHttpsMiddleware(object):
    """
    Sets no-cache headers when HTTPS META variable is set
    and not equal to 'off'.
    """
    def process_response(self, request, response):
        if request.is_secure():
            response['Expires'] = 'Thu, 19 Nov 1981 08:52:00 GMT'
            response['Cache-Control'] = 'no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
        return response


class PlusToSpaceMiddleware(object):
    """Replace old-style + with %20 in URLs."""
    def process_request(self, request):
        p = re.compile(r'\+')
        if p.search(request.path_info):
            new = p.sub(' ', request.path_info)
            if request.META['QUERY_STRING']:
                new = u'%s?%s' % (new,
                                  smart_unicode(request.META['QUERY_STRING']))
            if hasattr(request, 'LANGUAGE_CODE'):
                new = u'/%s%s' % (request.LANGUAGE_CODE, new)
            return HttpResponsePermanentRedirect(new)


class ReadOnlyMiddleware(object):

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
class DetectMobileMiddleware(object):
    """Looks at user agent and decides whether the device is mobile."""
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
