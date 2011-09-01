import inspect

from django.conf import settings
from django.http import HttpResponseRedirect


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


def for_all_methods(decorator):
    """A class decorator to apply a decorator to all its methods."""
    def decorate(cls):
        for method in inspect.getmembers(cls, inspect.ismethod):
            # Skip __dunder__ methods
            if not (method[0].startswith('__') and method[0].endswith('__')):
                setattr(cls, method[0], decorator(getattr(cls, method[0])))
        return cls
    return decorate
