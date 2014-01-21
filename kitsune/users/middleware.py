from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect

from tower import ugettext_lazy as _lazy

from kitsune.sumo.urlresolvers import reverse


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


class LogoutDeactivatedUsersMiddleware(object):
    """Verifies that user.is_active == True.

    If a user has been deactivated, we log them out.

    If a user isn't active but is in the AAQ process, we let them be.
    """
    def process_request(self, request):
        user = request.user

        if (user.is_authenticated() and not user.is_active
            and not request.session.get('in-aaq', False)):

            # The user is auth'd, not active and not in AAQ. /KICK
            logout(request)
            res = HttpResponseRedirect(reverse('home'))
            res.delete_cookie(settings.SESSION_EXISTS_COOKIE)
            return res
