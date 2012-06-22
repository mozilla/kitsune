import logging

from django import http
from django.conf import settings


log = logging.getLogger('k')

PREFIX = 'custcare_'
REDIRECT_NAME = PREFIX + 'redirect'
REQUEST_KEY_NAME = PREFIX + 'request_key'
REQUEST_SECRET_NAME = PREFIX + 'request_secret'

MAX_AGE = 3600


def url(request, override=None):
    d = {
        'scheme': 'https' if request.is_secure() else 'http',
        'host': request.get_host(),
        'path': request.get_full_path(),
    }
    if override:
        d.update(override)

    return u'%s://%s%s' % (d['scheme'], d['host'], d['path'])


def auth_wanted(view_func):
    """Twitter sessions are SSL only, so redirect to SSL if needed.

    Don't redirect if TWITTER_COOKIE_SECURE is False.
    """
    def wrapper(request, *args, **kwargs):
        is_secure = settings.TWITTER_COOKIE_SECURE
        if (request.COOKIES.get(REDIRECT_NAME) and
            (is_secure and not request.is_secure())):
            ssl_url = url(
                request,
                {'scheme': 'https' if is_secure else 'http'})
            return http.HttpResponseRedirect(ssl_url)

        return view_func(request, *args, **kwargs)
    return wrapper


def auth_required(view_func):
    """Return a HttpResponseBadRequest if not authed."""
    def wrapper(request, *args, **kwargs):

        if not request.twitter.authed:
            return http.HttpResponseBadRequest()

        return view_func(request, *args, **kwargs)
    return wrapper


class Session(object):
    key_key = 'twitter_oauth_key'
    key_secret = 'twitter_oauth_secret'

    @property
    def authed(self):
        return bool(self.key and self.secret)

    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret

    @classmethod
    def from_request(cls, request):
        s = cls()
        s.key = request.session.get(s.key_key)
        s.secret = request.session.get(s.key_secret)
        return s

    def delete(self, request, response):
        response.delete_cookie(REDIRECT_NAME)
        if self.key_key in request.session:
            del request.session[self.key_key]
        if self.key_secret in request.session:
            del request.session[self.key_secret]
        self.key = None
        self.secret = None

    def save(self, request, response):
        request.session[self.key_key] = self.key
        request.session[self.key_secret] = self.secret
        response.set_cookie(REDIRECT_NAME, '1', max_age=MAX_AGE)
