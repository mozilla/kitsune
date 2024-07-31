import json
import re
from functools import wraps

from csp.utils import build_policy
from django import http
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404

from kitsune.sumo.utils import is_ratelimited

from wagtail.views import serve as wagtail_serve


# Copy/pasta from from https://gist.github.com/1405096
# TODO: Log the hell out of the exceptions.
JSON = "application/json"


def json_view(f):
    """Ensure the response content is well-formed JSON.

    Views wrapped in @json_view can return JSON-serializable Python objects,
    like lists and dicts, and the decorator will serialize the output and set
    the correct Content-type.

    Views may also throw known exceptions, like Http404, PermissionDenied,
    etc, and @json_view will convert the response to a standard JSON error
    format, and set the status code and content type.

    """

    @wraps(f)
    def _wrapped(req, *a, **kw):
        try:
            ret = f(req, *a, **kw)
            blob = json.dumps(ret)
            return http.HttpResponse(blob, content_type=JSON)
        except http.Http404 as e:
            blob = json.dumps(
                {
                    "success": False,
                    "error": 404,
                    "message": str(e),
                }
            )
            return http.HttpResponseNotFound(blob, content_type=JSON)
        except PermissionDenied as e:
            blob = json.dumps(
                {
                    "success": False,
                    "error": 403,
                    "message": str(e),
                }
            )
            return http.HttpResponseForbidden(blob, content_type=JSON)
        except Exception as e:
            blob = json.dumps(
                {
                    "success": False,
                    "error": 500,
                    "message": str(e),
                }
            )
            return http.HttpResponseServerError(blob, content_type=JSON)

    return _wrapped


def cors_enabled(origin, methods=["GET"]):
    """A simple decorator to enable CORS."""

    def decorator(f):
        @wraps(f)
        def decorated_func(request, *args, **kwargs):
            if request.method == "OPTIONS":
                # preflight
                if (
                    "HTTP_ACCESS_CONTROL_REQUEST_METHOD" in request.META
                    and "HTTP_ACCESS_CONTROL_REQUEST_HEADERS" in request.META
                ):
                    response = http.HttpResponse()
                    response["Access-Control-Allow-Methods"] = ", ".join(methods)

                    # TODO: We might need to change this
                    response["Access-Control-Allow-Headers"] = request.META[
                        "HTTP_ACCESS_CONTROL_REQUEST_HEADERS"
                    ]
                else:
                    return http.HttpResponseBadRequest()
            elif request.method in methods:
                response = f(request, *args, **kwargs)
            else:
                return http.HttpResponseBadRequest()

            response["Access-Control-Allow-Origin"] = origin
            return response

        return decorated_func

    return decorator


def ratelimit(name, rate, method="POST"):
    """
    Reimplement ``ratelimit.decorators.ratelimit``, using a sumo-specic ``is_ratelimited``.

    This discards a lot of the flexibility of the original, and in turn is a lot simpler.
    """

    def _decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kwargs):
            # Sets ``request.limited`` on ``request``.
            is_ratelimited(request, name, rate, method)
            return fn(request, *args, **kwargs)

        return _wrapped

    return _decorator


def skip_if_read_only_mode(fn):
    """
    Ensures that the decorated function will be skipped if we're in read-only mode.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not settings.READ_ONLY:
            return fn(*args, **kwargs)

    return wrapper


def csp_allow_inline_scripts_and_styles(fn):
    """
    Add a CSP header to the response of the decorated view that allows inline
    scripts and styles. The CSP header is created from the CSP values in the
    settings, and then updated to include the "'unsafe-inline'" source within
    both the "style-src" and "script-src" directives. The CSP header is inserted
    in the response so that the normal insertion of the header within the
    CSPMiddleware is bypassed. That, in turn, prevents the CSPMiddleware from
    adding the nonce sources, which would override the "'unsafe-inline'" sources
    and effectively cause them to be ignored.
    """

    @wraps(fn)
    def wrapped(*args, **kwargs):
        response = fn(*args, **kwargs)
        response["Content-Security-Policy"] = build_policy(
            update={
                "style-src": "'unsafe-inline'",
                "script-src": "'unsafe-inline'",
            }
        )
        return response

    return wrapped


def remove_locale(url):
    # Define the regex pattern for locale (e.g., /en-US/ or /en-us/)
    locale_pattern = r"^/([a-z]{2}(-[a-zA-Z]{2})?)/"
    # Remove the locale part
    return re.sub(locale_pattern, "/", url)


def prefer_cms(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        path = remove_locale(request.path_info)
        try:
            wagtail_response = wagtail_serve(request, path)
            if wagtail_response.status_code == 200:
                return wagtail_response
        except Http404:
            pass  # Continue to the original view if no Wagtail page is found
        return view_func(request, *args, **kwargs)

    return _wrapped_view
