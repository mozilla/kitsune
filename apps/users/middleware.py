from django.conf import settings
from django.http import HttpResponseRedirect


class StaySecureMiddleware(object):
    """Detects a cookie indicating a user has a session and stays secure.

    Should be below ReverseProxyMiddleware if it's used.

    """
    def process_request(self, request):
        SEC = settings.SESSION_EXISTS_COOKIE
        need_https = settings.SESSION_COOKIE_SECURE and SEC in request.COOKIES
        if need_https and not request.is_secure():
            host = request.META['SERVER_NAME']
            path = request.META['PATH_INFO']
            qs = request.META['QUERY_STRING']
            if qs:
                path = u'%s?%s' % (path, qs)
            url = u'https://%s%s' % (host, path)
            return HttpResponseRedirect(url)
