from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from datetime import datetime

from kitsune.sumo.urlresolvers import reverse


class LogoutDeactivatedUsersMiddleware(object):
    """Verifies that user.is_active == True.

    If a user has been deactivated, we log them out.
    """
    def process_request(self, request):

        user = request.user

        if user.is_authenticated() and not user.is_active:

            logout(request)
            return HttpResponseRedirect(reverse('home'))


class LogoutInvalidatedSessionsMiddleware(object):
    """Logs out any sessions started before a user changed their
    Firefox Accounts password.
    """
    def process_request(self, request):

        user = request.user

        if user.is_authenticated():
            first_seen = request.session.get("first_seen")
            if first_seen:
                change_time = user.profile.password_change_time
                if change_time and change_time > first_seen:
                    logout(request)
                    return HttpResponseRedirect(reverse('home'))
            else:
                request.session["first_seen"] = datetime.utcnow()


# NOTE: This middleware should be removed in May 2020
# where all active sessions for sumo accounts will have expired.
class LogoutSumoAccountsMiddleware(object):
    """Logs out any users that are active in the site with SUMO accounts."""

    def process_request(self, request):

        user = request.user
        if (user.is_authenticated() and user.profile and not user.profile.is_fxa_migrated):

            # The user is auth'd, not active and not in AAQ. /KICK
            logout(request)
            return HttpResponseRedirect(reverse('home'))
