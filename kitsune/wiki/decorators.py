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
            url = reverse(
                'wiki.document', args=[SIMPLE_WIKI_LANDING_PAGE_SLUG])
            return http.HttpResponseRedirect(url)

        return view_func(request, *args, **kwargs)

    return _check_simple_wiki_locale
