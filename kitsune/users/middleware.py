from datetime import datetime

from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

from kitsune.sumo.urlresolvers import reverse


class LogoutDeactivatedUsersMiddleware(MiddlewareMixin):
    """Verifies that user.is_active == True.

    If a user has been deactivated, we log them out.
    """
    def process_request(self, request):

        user = request.user

        if user.is_authenticated and not user.is_active:

            logout(request)
            return HttpResponseRedirect(reverse('home'))


class LogoutInvalidatedSessionsMiddleware(MiddlewareMixin):
    """Logs out any sessions started before a user changed their
    Firefox Accounts password.
    """
    def process_request(self, request):

        user = request.user

        # TODO: py3 upgrade: change to is_authenticated attribute
        if user.is_authenticated():
            first_seen = request.session.get("first_seen")
            if first_seen:
                change_time = user.profile.fxa_password_change
                if change_time and change_time > first_seen:
                    logout(request)
                    return HttpResponseRedirect(reverse('home'))
            else:
                request.session["first_seen"] = datetime.utcnow()
