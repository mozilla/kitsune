from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

from kitsune.sumo.urlresolvers import reverse


class LogoutDeactivatedUsersMiddleware(object):
    """Verifies that user.is_active == True.

    If a user has been deactivated, we log them out.

    If a user isn't active but is in the AAQ process, we let them be.
    """
    def process_request(self, request):

        user = request.user

        if (user.is_authenticated() and not user.is_active and
                not request.session.get('in-aaq', False)):

            # The user is auth'd, not active and not in AAQ. /KICK
            logout(request)
            return HttpResponseRedirect(reverse('home'))


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
