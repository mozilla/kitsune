import logging
from uuid import uuid4

from django import http
from django.conf import settings


log = logging.getLogger('k')

PREFIX = 'custcare_'
ACCESS_NAME = PREFIX + 'access'
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

    Don't redirect if TWITTER_COOKIE_SECURE is False."""
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
    id = None
    key = None
    secret = None

    @property
    def cachekey_key(self):
        return '{0}_key_{1}'.format(ACCESS_NAME, self.id)

    @property
    def cachekey_secret(self):
        return '{0}_secret_{1}'.format(ACCESS_NAME, self.id)

    @property
    def authed(self):
        return bool(self.id and self.key and self.secret)

    def __init__(self, key=None, secret=None):
        self.id = uuid4().hex
        self.key = key
        self.secret = secret

    @classmethod
    def from_request(cls, request):
        s = cls()
        s.id = request.session.get(ACCESS_NAME)
        s.key = request.session.get(s.cachekey_key)
        s.secret = request.session.get(s.cachekey_secret)
        return s

    def delete(self, request, response):
        response.delete_cookie(REDIRECT_NAME)
        if ACCESS_NAME in request.session:
            del request.session[ACCESS_NAME]
        if self.cachekey_key in request.session:
            del request.session[self.cachekey_key]
        if self.cachekey_secret in request.session:
            del request.session[self.cachekey_secret]
        self.id = None
        self.key = None
        self.secret = None

    def save(self, request, response):
        request.session[self.cachekey_key] = self.key
        request.session[self.cachekey_secret] = self.secret
        request.session[ACCESS_NAME] = self.id
        response.set_cookie(REDIRECT_NAME, '1', max_age=MAX_AGE)
