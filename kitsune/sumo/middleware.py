import contextlib
import re
import time
from functools import wraps

import django.middleware.locale
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import BACKEND_SESSION_KEY, logout
from django.core.exceptions import MiddlewareNotUsed
from django.core.validators import ValidationError, validate_ipv4_address
from django.db.utils import DatabaseError
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.http.request import split_domain_port
from django.shortcuts import render
from django.urls import is_valid_path
from django.utils import translation
from django.utils.cache import add_never_cache_headers, patch_response_headers, patch_vary_headers
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import iri_to_uri, smart_str
from enforce_host import EnforceHostMiddleware
from mozilla_django_oidc.middleware import SessionRefresh

from kitsune.sumo.i18n import get_language_from_user, normalize_language, normalize_path
from kitsune.sumo.views import handle403
from kitsune.users.auth import FXAAuthBackend


class EnforceHostIPMiddleware(EnforceHostMiddleware):
    """Modify the `EnforceHostMiddleware` to allow IP addresses"""

    def __call__(self, request):
        host = request.get_host()
        domain, _ = split_domain_port(host)
        try:
            validate_ipv4_address(domain)
        except ValidationError:
            # not an IP address. Call the superclass
            return super().__call__(request)

        # it is an IP address
        return self.get_response(request)


class HttpResponseRateLimited(HttpResponse):
    status_code = 429


class SUMORefreshIDTokenAdminMiddleware(SessionRefresh):
    def __init__(self, get_response=None):
        if not settings.OIDC_ENABLE or settings.DEV:
            raise MiddlewareNotUsed
        super(SUMORefreshIDTokenAdminMiddleware, self).__init__(get_response=get_response)

    def process_request(self, request):
        """Only allow refresh and enforce OIDC auth on admin URLs"""
        # If the admin is targeted let's check the backend used, if any
        if request.path.startswith("/admin/") and request.path != "/admin/login/":
            backend = request.session.get(BACKEND_SESSION_KEY)
            if backend and backend.split(".")[-1] != "SumoOIDCAuthBackend":
                logout(request)
                messages.error(request, "OIDC login required for admin access")
                return HttpResponseRedirect("/admin/login/")

            return super(SUMORefreshIDTokenAdminMiddleware, self).process_request(request)


class ValidateAccessTokenMiddleware(SessionRefresh):
    """Validate the ID Token from FxA every hour."""

    def __init__(self, get_response=None):
        if not settings.OIDC_ENABLE or settings.DEV:
            raise MiddlewareNotUsed
        super(ValidateAccessTokenMiddleware, self).__init__(get_response=get_response)

    def process_request(self, request):
        """Check the validity of the access_token.

        Check is performed at FXA_RENEW_ID_TOKEN_EXPIRY_SECONDS intervals.
        """
        if not self.is_refreshable_url(request):
            return

        # the oidc_id_token_expiration key is set by the mozilla-django-oidc library
        expiration = request.session.get("oidc_id_token_expiration", 0)
        now = time.time()
        access_token = request.session.get("oidc_access_token")
        profile = request.user.profile

        if access_token and expiration < now:
            token_info = FXAAuthBackend.refresh_access_token(profile.fxa_refresh_token)
            new_access_token = token_info.get("access_token")
            if new_access_token:
                request.session["oidc_access_token"] = new_access_token
                request.session["oidc_id_token_expiration"] = (
                    now + settings.FXA_RENEW_ID_TOKEN_EXPIRY_SECONDS
                )
            else:
                profile.fxa_refresh_token = ""
                profile.save()
                logout(request)


class LocaleMiddleware(django.middleware.locale.LocaleMiddleware):
    def process_request(self, request):
        # Handle redirects requested via the "lang" query parameter, which overrides
        # everything, even the language in the path.
        if normalized_lang := normalize_language(request.GET.get("lang")):
            new_full_path = normalize_path(request.path_info, force_language=normalized_lang)

            # Remove "lang" from the query parameters, so we don't create an infinite loop,
            # and if any query parameters remain, add them back to the new full path.
            query = request.GET.copy()
            query.pop("lang")
            if query:
                new_full_path += f"?{query.urlencode()}"

            if request.user.is_anonymous:
                request.session[settings.LANGUAGE_COOKIE_NAME] = normalized_lang

            return HttpResponseRedirect(new_full_path)

        # Handle redirects due to normalization, supported variants, and explicit fallbacks.
        if request.path_info != (new_full_path := normalize_path(request.path_info)):
            if request.GET:
                new_full_path += f"?{request.GET.urlencode()}"
            return HttpResponseRedirect(new_full_path)

        with normalized_get_language():
            response = super().process_request(request)

        # Django won't check for a language code in SUMO's user-related sources, so
        # let's check for that now. If there wasn't a supported language in the path,
        # but there was a supported language in one of the user-related sources, we'll
        # override Django's selected language with that one if it's different.
        if (
            (language_from_user := get_language_from_user(request))
            and (language_from_user != request.LANGUAGE_CODE)
            and not (translation.get_language_from_path(request.path_info))
        ):
            translation.activate(language_from_user)
            request.LANGUAGE_CODE = language_from_user

        return response

    def process_response(self, request, response):
        with normalized_get_language():
            return super().process_response(request, response)


@contextlib.contextmanager
def normalized_get_language():
    """
    Ensures that any use of django.utils.translation.get_language()
    within its context will return a normalized language code. This
    context manager only works when the "get_language" function is
    acquired from the "django.utils.translation" module at call time,
    so for example, if it's called like "translation.get_language()".
    """
    get_language = translation.get_language

    @wraps(get_language)
    def get_normalized_language():
        return normalize_language(get_language())

    translation.get_language = get_normalized_language

    try:
        yield
    finally:
        translation.get_language = get_language


class Forbidden403Middleware(MiddlewareMixin):
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

    def __init__(self, get_response=None):
        super(VaryNoCacheMiddleware, self).__init__(get_response=get_response)
        if not settings.ENABLE_VARY_NOCACHE_MIDDLEWARE:
            raise MiddlewareNotUsed

    @staticmethod
    def process_response(request, response):
        if "vary" in response and "accept-language" in response["vary"].lower():
            add_never_cache_headers(response)

        return response


class CacheHeadersMiddleware(MiddlewareMixin):
    """
    Sets no-cache headers normally, and cache for some time in READ_ONLY mode.
    """

    def process_response(self, request, response):
        if "cache-control" in response or response.status_code >= 400:
            return response

        if request.method in ("GET", "HEAD") and settings.CACHE_MIDDLEWARE_SECONDS:
            # uses CACHE_MIDDLEWARE_SECONDS by default
            patch_response_headers(response)
        else:
            add_never_cache_headers(response)

        return response


class PlusToSpaceMiddleware(MiddlewareMixin):
    """Replace old-style + with %20 in URLs."""

    def process_request(self, request):
        p = re.compile(r"\+")
        if p.search(request.path_info):
            new = p.sub(" ", request.path_info)
            if request.META.get("QUERY_STRING"):
                new = "%s?%s" % (new, smart_str(request.META["QUERY_STRING"]))
            if hasattr(request, "LANGUAGE_CODE"):
                new = "/%s%s" % (request.LANGUAGE_CODE, new)
            return HttpResponsePermanentRedirect(new)


class ReadOnlyMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super(ReadOnlyMiddleware, self).__init__(get_response=get_response)
        if not settings.READ_ONLY:
            raise MiddlewareNotUsed

    def process_request(self, request):
        if request.method == "POST":
            return render(request, "sumo/read-only.html", status=503)

    def process_exception(self, request, exception):
        if isinstance(exception, DatabaseError):
            return render(request, "sumo/read-only.html", status=503)


class RemoveSlashMiddleware(MiddlewareMixin):
    """
    Middleware that tries to remove a trailing slash if there was a 404.

    If the response is a 404 because url resolution failed, we'll look for a
    better url without a trailing slash.
    """

    def __init__(self, get_response):
        super(RemoveSlashMiddleware, self).__init__(get_response)

    def process_response(self, request, response):
        if (
            response.status_code == 404
            and request.path_info.endswith("/")
            and not is_valid_path(request.path_info)
            and is_valid_path(request.path_info[:-1])
        ):
            # Use request.path because we munged app/locale in path_info.
            newurl = request.path[:-1]
            if request.GET:
                with safe_query_string(request):
                    newurl += "?" + request.META["QUERY_STRING"]
            return HttpResponsePermanentRedirect(newurl)
        return response


@contextlib.contextmanager
def safe_query_string(request):
    """
    Turn the QUERY_STRING into a unicode- and ascii-safe string.

    We need unicode so it can be combined with a reversed URL, but it has to be
    ascii to go in a Location header.  iri_to_uri seems like a good compromise.
    """
    qs = request.META["QUERY_STRING"]
    try:
        request.META["QUERY_STRING"] = iri_to_uri(qs)
        yield
    finally:
        request.META["QUERY_STRING"] = qs


class HostnameMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super(HostnameMiddleware, self).__init__(get_response=get_response)
        if getattr(settings, "DISABLE_HOSTNAME_MIDDLEWARE", False):
            raise MiddlewareNotUsed()

        values = [getattr(settings, x) for x in ["PLATFORM_NAME", "K8S_DOMAIN"]]
        self.backend_server = ".".join(x for x in values if x)

    def process_response(self, request, response):
        response["X-Backend-Server"] = self.backend_server
        return response


class FilterByUserAgentMiddleware(MiddlewareMixin):
    """Looks at user agent and decides whether the device is allowed on the site."""

    def __init__(self, get_response=None):
        super(FilterByUserAgentMiddleware, self).__init__(get_response=get_response)
        if not settings.USER_AGENT_FILTERS:
            raise MiddlewareNotUsed()

    def process_request(self, request):
        client_ua = request.META.get("HTTP_USER_AGENT", "").lower()
        # get only ascii chars
        ua = "".join(i for i in client_ua if ord(i) < 128)

        if any(x in ua for x in settings.USER_AGENT_FILTERS):
            response = HttpResponseRateLimited()
            patch_vary_headers(response, ["User-Agent"])
            return response


class InAAQMiddleware(MiddlewareMixin):
    """
    Middleware that clears AAQ data from the session under certain conditions.
    """

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if not request.session or not callback:
            return None
        try:
            view_name = callback.__name__
        except AttributeError:
            return None

        # If we are authenticating or there is no session, do nothing
        if view_name in ["user_auth", "login", "serve_cors"]:
            return None
        if "aaq" not in view_name:
            if ("/questions/new" not in request.META.get("HTTP_REFERER", "")) or (
                "exit_aaq" in request.GET
            ):
                request.session["aaq_context"] = {}
        return None
