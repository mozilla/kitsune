from django.contrib.auth import authenticate, login
from django.contrib import messages

from tower import ugettext_lazy as _lazy


class TokenLoginMiddleware(object):
    """Allows users to be logged in via one time tokens."""

    def process_request(self, request):

        auth = request.GET.get('auth')
        if auth is None or request.user.is_authenticated():
            return
        user = authenticate(auth=auth)
        if user and user.is_active:
            login(request, user)
            msg = _lazy(u'You have been automatically logged in.')
            messages.success(request, msg)
