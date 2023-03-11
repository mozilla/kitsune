from datetime import datetime

from django.contrib import auth
from django.contrib.auth import middleware
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import LightUser


def get_user(request):
    if not hasattr(request, "_cached_user"):
        request._cached_user = LightUser.get_user(request) or auth.get_user(request)
    return request._cached_user


class AuthenticationMiddleware(middleware.AuthenticationMiddleware):
    def process_request(self, request):
        if not hasattr(request, "session"):
            raise ImproperlyConfigured(
                "The authentication middleware must be preceded by "
                "session middleware within the MIDDLEWARE setting."
            )
        request.user = SimpleLazyObject(lambda: get_user(request))


class LogoutDeactivatedUsersMiddleware(MiddlewareMixin):
    """Verifies that user.is_active == True.

    If a user has been deactivated, we log them out.
    """

    def process_request(self, request):
        user = request.user

        if user.is_authenticated and not user.is_active:
            auth.logout(request)
            return HttpResponseRedirect(reverse("home"))


class LogoutInvalidatedSessionsMiddleware(MiddlewareMixin):
    """Logs out any sessions started before a user changed their
    Firefox Accounts password.
    """

    def process_request(self, request):
        user = request.user

        if user.is_authenticated:
            first_seen = request.session.get("first_seen")
            if first_seen:
                change_time = user.profile.fxa_password_change
                if change_time and change_time > first_seen:
                    auth.logout(request)
                    return HttpResponseRedirect(reverse("home"))
            else:
                request.session["first_seen"] = datetime.utcnow()
