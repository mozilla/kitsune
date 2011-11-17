import json

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse


def ssl_required(view_func):
    """A view decorator that enforces HTTPS.

    If settings.DEBUG is True, it doesn't enforce anything."""
    def _checkssl(request, *args, **kwargs):
        if not settings.DEBUG and not request.is_secure():
            url_str = request.build_absolute_uri()
            url_str = url_str.replace('http://', 'https://')
            return HttpResponseRedirect(url_str)

        return view_func(request, *args, **kwargs)
    return _checkssl


# Modified version of http://djangosnippets.org/snippets/2102/
def render_to_json(view_func):
    """
    Renders a JSON response with a given returned instance. Assumes
    json.dumps() can handle the result.

    @render_to_json
    def a_view(request, arg1, argN):
        ...
        return {'x': range(4)}
    """
    def inner_json(request, *args, **kwargs):
        result = view_func(request, *args, **kwargs)
        r = HttpResponse(mimetype='application/json')
        if result:
            r.write(json.dumps(result))
        else:
            r.write("{}")
        return r
    return inner_json
