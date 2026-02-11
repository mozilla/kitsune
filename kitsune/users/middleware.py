from datetime import datetime

from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now as timezone_now

from kitsune.sumo.urlresolvers import reverse


class LogoutDeactivatedUsersMiddleware(MiddlewareMixin):
    """Verifies that user.is_active == True.

    If a user has been deactivated, we log them out.
    """

    def process_request(self, request):
        user = request.user

        if user.is_authenticated and not user.is_active:
            logout(request)
            return HttpResponseRedirect(reverse("home"))


class LogoutInvalidatedSessionsMiddleware(MiddlewareMixin):
    """Logs out any sessions started before a user changed their
    Mozilla account password.
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        match request.session.get("first_seen"):
            case str() as first_seen:
                try:
                    first_seen = datetime.fromisoformat(first_seen)
                except ValueError:
                    first_seen = None
            case datetime() as first_seen:
                # Legacy pickle-serialized datetime object.
                pass
            case _:
                first_seen = None

        if first_seen is None:
            request.session["first_seen"] = timezone_now().isoformat()
            return

        change_time = request.user.profile.fxa_password_change
        if change_time and change_time > first_seen:
            logout(request)
            return HttpResponseRedirect(reverse("home"))
