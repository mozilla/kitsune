import logging

import requests
from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth.signals import user_logged_in

from django.middleware.csrf import rotate_token
from django.urls import reverse as django_reverse
from django.utils.translation import activate
from django.utils.translation import gettext as _
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from kitsune.customercare.tasks import update_zendesk_identity
from kitsune.users.models import UserProxy
from kitsune.users.utils import add_to_contributors, get_oidc_fxa_setting

log = logging.getLogger("k.users")


SESSION_KEY = "kitsune_user_key"
BACKEND_SESSION_KEY = "kitsune_user_backend"


class SumoOIDCAuthBackend(OIDCAuthenticationBackend):
    def authenticate(self, request, **kwargs):
        """Authenticate a user based on the OIDC code flow."""

        # If the request has the /fxa/callback/ path then probably there is a login
        # with Firefox Accounts. In this case just return None and let
        # the FxA backend handle this request.
        if request and not request.path == django_reverse("oidc_authentication_callback"):
            return None

        return super(SumoOIDCAuthBackend, self).authenticate(request, **kwargs)

    def get_user(self, user_key):
        return UserProxy.get_user_from_key(user_key)


class FXAAuthBackend(OIDCAuthenticationBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh_token = None

    @staticmethod
    def get_settings(attr, *args):
        """Override settings for Firefox Accounts Provider."""
        val = get_oidc_fxa_setting(attr)
        if val is not None:
            return val
        return super(FXAAuthBackend, FXAAuthBackend).get_settings(attr, *args)

    def get_token(self, payload):
        token_info = super().get_token(payload)
        self.refresh_token = token_info.get("refresh_token")
        return token_info

    @classmethod
    def refresh_access_token(cls, refresh_token, ttl=None):
        """Gets a new access_token by using a refresh_token.

        returns: the actual token or an empty dictionary
        """

        if not refresh_token:
            return {}

        obj = cls()
        payload = {
            "client_id": obj.OIDC_RP_CLIENT_ID,
            "client_secret": obj.OIDC_RP_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        if ttl:
            payload.update({"ttl": ttl})

        try:
            return obj.get_token(payload=payload)
        except requests.exceptions.HTTPError:
            return {}

    def update_contributor_status(self, profile):
        """Register user as contributor."""
        # The request attribute might not be set.
        request = getattr(self, "request", None)
        if request and (contribution_area := request.session.get("contributor")):
            add_to_contributors(profile.user, profile.locale, contribution_area)
            del request.session["contributor"]

    def create_user(self, claims):
        """Override create user method to mark the profile as migrated."""
        fxa_uid = claims.get("uid")

        if not fxa_uid:
            return None

        # A few assertions return a locale of None so we need to default to empty string
        for locale in (claims.get("locale") or "").split(","):
            if locale in settings.SUMO_LANGUAGES:
                break
        else:
            locale = self.request.session.get("login_locale", settings.LANGUAGE_CODE)

        activate(locale)

        # The user's information is saved in the cache, and is only a reflection of
        # what we get from FxA. It should only be changed in FxA, not SUMO.
        user = UserProxy(
            fxa_uid=fxa_uid,
            email=claims.get("email"),
            username=self.get_username(claims),
            name=claims.get("displayName", ""),
            fxa_avatar=claims.get("avatar", ""),
            subscriptions=claims.get("subscriptions", []),
            fxa_refresh_token=self.refresh_token or "",
            locale=locale,
            zendesk_id="",
        )
        user.save()

        messages.success(
            self.request,
            _("<strong>Welcome!</strong> You are now logged in using Firefox Accounts."),
            extra_tags="safe",
        )

        return user

    def filter_users_by_claims(self, claims):
        """Match a user by FxA uid"""
        # Something went terribly wrong. Return an empty list.
        if not (fxa_uid := claims.get("uid")):
            log.warning("Failed to get Firefox Account UID.")
            return []

        if not (user := UserProxy.get_user_from_fxa_uid(fxa_uid)):
            return []

        return [user]

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details and subscription information dictionary."""

        user_info = super(FXAAuthBackend, self).get_userinfo(access_token, id_token, payload)

        if not settings.FXA_OP_SUBSCRIPTION_ENDPOINT:
            return user_info

        # Fetch subscription information
        try:
            sub_response = requests.get(
                settings.FXA_OP_SUBSCRIPTION_ENDPOINT,
                headers={"Authorization": "Bearer {0}".format(access_token)},
                verify=self.get_settings("OIDC_VERIFY_SSL", True),
            )
            sub_response.raise_for_status()
        except requests.exceptions.RequestException:
            log.error("Failed to fetch subscription status", exc_info=True)
            # if something went wrong, just return whatever the profile endpoint holds
            return user_info
        # This will override whatever the profile endpoint returns
        # until https://github.com/mozilla/fxa/issues/2463 is fixed
        user_info["subscriptions"] = sub_response.json().get("subscriptions", [])
        return user_info

    def update_user(self, user, claims):
        """Update existing user with new claims, if necessary save, and return user"""

        attrs_to_check = {}
        attrs_changed = set()

        for locale in (claims.get("locale") or "").split(","):
            if locale in settings.SUMO_LANGUAGES:
                attrs_to_check["locale"] = locale
                break

        attrs_to_check["fxa_uid"] = claims.get("uid")
        attrs_to_check["email"] = claims.get("email")
        attrs_to_check["username"] = self.get_username(claims)
        attrs_to_check["fxa_avatar"] = claims.get("avatar", "")
        attrs_to_check["name"] = claims.get("displayName", "")
        attrs_to_check["subscriptions"] = claims.get("subscriptions", [])

        if self.refresh_token:
            attrs_to_check["fxa_refresh_token"] = self.refresh_token

        for name, value in attrs_to_check.items():
            if getattr(user, name) != value:
                setattr(user, name, value)
                attrs_changed.add(name)

        # TODO: If we need to take this POC further.
        # self.update_contributor_status(profile)

        if attrs_changed:
            user.save()

        # If we have an updated email, let's update Zendesk too
        # the check is repeated for now but it will save a few
        # API calls if we trigger the task only when we know that we have new emails
        if ("email" in attrs_changed) and user.zendesk_id:
            update_zendesk_identity.delay(user.key, user.email)

        return user

    def authenticate(self, request, **kwargs):
        """Authenticate a user based on the OIDC/oauth2 code flow."""

        # If the request has the /oidc/callback/ path then probably there is a login
        # attempt in the admin interface. In this case just return None and let
        # the OIDC backend handle this request.
        if request and request.path == django_reverse("oidc_authentication_callback"):
            return None

        return super(FXAAuthBackend, self).authenticate(request, **kwargs)

    def get_user(self, user_key):
        return UserProxy.get_user_from_key(user_key)


def login(request, user, backend=None):
    """
    Persist a user key and a backend in the request. This way a user doesn't
    have to reauthenticate on every request. Note that data set during
    the anonymous session is retained when the user logs in.
    """
    if SESSION_KEY in request.session:
        if request.session[SESSION_KEY] != user.key:
            # To avoid reusing another user's session, create a new, empty
            # session if the existing session corresponds to a different
            # authenticated user.
            request.session.flush()
    else:
        request.session.cycle_key()

    request.session[SESSION_KEY] = user.key
    request.session[BACKEND_SESSION_KEY] = backend or user.backend
    if hasattr(request, "user"):
        request.user = user
    rotate_token(request)
    user_logged_in.send(sender=user.__class__, request=request, user=user)


def get_user(request):
    """
    Return the user associated with the given request session.
    If no user is retrieved, return an instance of `AnonymousUser`.
    """
    from django.contrib.auth.models import AnonymousUser

    user = None
    try:
        user_key = request.session[SESSION_KEY]
        backend_path = request.session[BACKEND_SESSION_KEY]
    except KeyError:
        pass
    else:
        if backend_path in settings.AUTHENTICATION_BACKENDS:
            backend = auth.load_backend(backend_path)
            user = backend.get_user(user_key)

    return user or AnonymousUser()
