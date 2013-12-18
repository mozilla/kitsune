from django.contrib import messages
from django.contrib.auth import authenticate, login

from tower import ugettext_lazy as _lazy


class TokenLoginMiddleware(object):
    """Allows users to be logged in via one time tokens."""

    def process_request(self, request):
        try:
            auth = request.GET.get('auth')
        except IOError:
            # Django can throw an IOError when trying to read the GET
            # data.
            return

        if auth is None or (request.user and request.user.is_authenticated()):
            return
        user = authenticate(auth=auth)
        if user and user.is_active:
            login(request, user)
            msg = _lazy(u'You have been automatically logged in.')
            messages.success(request, msg)
