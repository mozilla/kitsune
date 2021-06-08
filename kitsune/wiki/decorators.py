from functools import wraps

from django import http
from django.conf import settings

from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import SIMPLE_WIKI_LANDING_PAGE_SLUG


def check_simple_wiki_locale(view_func):
    """A view decorator that redirects configured locales to FAQ wiki page"""

    @wraps(view_func)
    def _check_simple_wiki_locale(request, *args, **kwargs):
        if request.LANGUAGE_CODE in settings.SIMPLE_WIKI_LANGUAGES:
            url = reverse("wiki.document", args=[SIMPLE_WIKI_LANDING_PAGE_SLUG])
            return http.HttpResponseRedirect(url)

        return view_func(request, *args, **kwargs)

    return _check_simple_wiki_locale


def edit_routing_behavior(skip=False, raise_404=True, redirect=True):
    """Edit the behavior of WikiRoutingMiddleware for the decorated view."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            return view_func(*args, **kwargs)

        wrapped_view.wiki_routing_skip = skip
        wrapped_view.wiki_routing_raise_404 = raise_404
        wrapped_view.wiki_routing_redirect = redirect
        return wrapped_view

    return decorator
