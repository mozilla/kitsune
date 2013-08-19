from functools import wraps
import json

from django import http
from django.conf import settings
from django.core.exceptions import PermissionDenied


def ssl_required(view_func):
    """A view decorator that enforces HTTPS.

    If settings.DEBUG is True, it doesn't enforce anything."""
    def _checkssl(request, *args, **kwargs):
        if not settings.DEBUG and not request.is_secure():
            url_str = request.build_absolute_uri()
            url_str = url_str.replace('http://', 'https://')
            return http.HttpResponseRedirect(url_str)

        return view_func(request, *args, **kwargs)
    return _checkssl


# Copy/pasta from from https://gist.github.com/1405096
# TODO: Log the hell out of the exceptions.
JSON = 'application/json'


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
        except http.Http404, e:
            blob = json.dumps({
                'success': False,
                'error': 404,
                'message': str(e),
            })
            return http.HttpResponseNotFound(blob, content_type=JSON)
        except PermissionDenied, e:
            blob = json.dumps({
                'success': False,
                'error': 403,
                'message': str(e),
            })
            return http.HttpResponseForbidden(blob, content_type=JSON)
        except Exception, e:
            blob = json.dumps({
                'success': False,
                'error': 500,
                'message': str(e),
            })
            return http.HttpResponseServerError(blob, content_type=JSON)
    return _wrapped


def cors_enabled(origin, methods=['GET']):
    """A simple decorator to enable CORS."""
    def decorator(f):
        @wraps(f)
        def decorated_func(request, *args, **kwargs):
            if request.method == 'OPTIONS':
                # preflight
                if ('HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META and
                    'HTTP_ACCESS_CONTROL_REQUEST_HEADERS' in request.META):

                    response = http.HttpResponse()
                    response['Access-Control-Allow-Methods'] = ", ".join(
                        methods)

                    # TODO: We might need to change this
                    response['Access-Control-Allow-Headers'] = \
                        request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']
                else:
                    return http.HttpResponseBadRequest()
            elif request.method in methods:
                response = f(request, *args, **kwargs)
            else:
                return http.HttpResponseBadRequest()

            response['Access-Control-Allow-Origin'] = origin
            return response
        return decorated_func
    return decorator
