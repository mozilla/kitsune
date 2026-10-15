import logging

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.db import transaction
from django.urls import reverse as django_reverse
from django.utils.translation import activate
from django.utils.translation import gettext as _
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from kitsune.customercare.tasks import update_zendesk_identity
from kitsune.groups.invitations import claim_enterprise_invitation, invitation_error
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.products.models import Product
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Profile
from kitsune.users.utils import add_to_contributors, get_oidc_fxa_setting

log = logging.getLogger("k.users")


def is_mozilla_domain_email(email: str) -> bool:
    """Check if the email domain is in the MOZILLA_DOMAINS list."""
    if not email:
        return False

    domain = email.rsplit("@", maxsplit=1)[-1].lower()
    return domain in [d.lower() for d in settings.MOZILLA_DOMAINS]


class SumoOIDCAuthBackend(OIDCAuthenticationBackend):
    def authenticate(self, request, **kwargs):
        """Authenticate a user based on the OIDC code flow."""

        # If the request has the /fxa/callback/ path then probably there is a login
        # with Mozilla accounts. In this case just return None and let
        # the FxA backend handle this request.
        if request and not request.path == django_reverse("oidc_authentication_callback"):
            return None

        return super().authenticate(request, **kwargs)


class FXAAuthBackend(OIDCAuthenticationBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh_token = None

    @staticmethod
    def get_settings(attr, *args):
        """Override settings for Mozilla accounts Provider."""
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
        """Recheck identity after locking; another signup or invitation may have won."""
        email = claims.get("email")
        with (
            lock_account_email(email) if email else transaction.atomic(),
            lock_enterprise_hierarchy(),
        ):
            users = self.filter_users_by_claims(claims)
            if len(users) == 1:
                return self._update_user(users[0], claims)
            if users:
                raise SuspiciousOperation("Multiple users returned")
            user = super().create_user(claims)
            profile, _created = Profile.objects.get_or_create(user=user)
            profile.is_fxa_migrated = True
            profile.fxa_uid = claims.get("uid")
            profile.fxa_avatar = claims.get("avatar", "")
            profile.name = claims.get("displayName", "")
            subscriptions = claims.get("subscriptions", [])

            if email := claims.get("email"):
                profile.is_mozilla_staff = is_mozilla_domain_email(email)

            # A few assertions return a locale of None so we need to default to empty string
            fxa_locale = (claims.get("locale", "") or "").split(",")[0]
            if fxa_locale in settings.SUMO_LANGUAGES:
                profile.locale = fxa_locale
            else:
                profile.locale = self.request.session.get("login_locale", settings.LANGUAGE_CODE)
            activate(profile.locale)

            if self.refresh_token:
                profile.fxa_refresh_token = self.refresh_token
            profile.save()
            products = Product.active.filter(codename__in=subscriptions)
            profile.products.set(products)

            messages.success(
                self.request,
                _(
                    "<strong>Welcome!</strong> You are now signed in using your Mozilla account. "
                    + "{a_profile}Edit your profile.{a_close}<br>"
                    + "Already have a different Mozilla Support Account? "
                    + "{a_more}Read more.{a_close}"
                ).format(
                    a_profile='<a href="'
                    + reverse("users.edit_my_profile")
                    + '" target="_blank">',
                    a_more='<a href="'
                    + reverse("wiki.document", args=["firefox-accounts-mozilla-support-faq"])
                    + '" target="_blank">',
                    a_close="</a>",
                ),
                extra_tags="safe",
            )

            self.update_contributor_status(profile)

            return user

    def get_or_create_user(self, access_token, id_token, payload):
        request = getattr(self, "request", None)
        token = getattr(request, "enterprise_invitation_token", None)
        if token is None:
            return super().get_or_create_user(access_token, id_token, payload)

        claims = self.get_userinfo(access_token, id_token, payload)
        if not self.verify_claims(claims):
            raise SuspiciousOperation("Claims verification failed")
        try:
            # Acceptance and the profile refresh commit together.
            with transaction.atomic():
                user = claim_enterprise_invitation(token, claims)
                user = self.update_user(user, claims)
                if user is None:
                    raise invitation_error("account_conflict")
                locale = (claims.get("locale") or "").split(",")[0]
                if locale in settings.SUMO_LANGUAGES:
                    user.profile.locale = locale
                    user.profile.save(update_fields=["locale"])
        except ValidationError as error:
            request.enterprise_invitation_error = error.code
            return None
        activate(user.profile.locale)
        return user

    def filter_users_by_claims(self, claims):
        """Match users by FxA uid or email."""
        fxa_uid = claims.get("uid")
        user_model = get_user_model()
        users = user_model.all_users.none()

        if fxa_uid:
            users = user_model.all_users.filter(profile__fxa_uid=fxa_uid)
        else:
            log.warning("Failed to get Mozilla account UID.")

        if not users:
            email = claims.get("email")
            if email:
                users = user_model.all_users.filter(email__iexact=email.strip())
        return users

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details and subscription information dictionary."""

        user_info = super().get_userinfo(access_token, id_token, payload)

        if not settings.FXA_OP_SUBSCRIPTION_ENDPOINT:
            return user_info

        # Fetch subscription information
        try:
            sub_response = requests.get(
                settings.FXA_OP_SUBSCRIPTION_ENDPOINT,
                headers={"Authorization": "Bearer {}".format(access_token)},
                verify=self.get_settings("OIDC_VERIFY_SSL", True),
            )
            sub_response.raise_for_status()
        except requests.exceptions.RequestException:
            log.error("Failed to fetch subscription status", exc_info=True)
            return user_info
        sub_status = sub_response.json().get("subscriptionsByClientId", {})
        user_info["subscriptions"] = list({v[0] for v in sub_status.values() if v})
        return user_info

    def update_user(self, user, claims):
        """Serialize destination-email updates, including background profile events."""
        email = claims.get("email")
        with (
            lock_account_email(email) if email else transaction.atomic(),
            lock_enterprise_hierarchy(),
        ):
            return self._update_user(user, claims)

    def _update_user(self, user, claims):
        # Lookup may predate the email lock; also discard any cached profile.
        user.refresh_from_db(from_queryset=User.all_users.select_for_update())
        profile = user.profile
        if profile.account_type == Profile.AccountType.SYSTEM:
            raise SuspiciousOperation("System accounts cannot sign in with Mozilla accounts")
        request = getattr(self, "request", None)
        if profile.is_unclaimed_invitee:
            if request:
                messages.error(
                    request,
                    _(
                        "This account was prepared through an enterprise invitation. "
                        "Use your invitation to sign in."
                    ),
                )
            raise SuspiciousOperation("Enterprise invitation required")

        email = claims.get("email")
        user_attr_changed = False
        subscriptions = claims.get("subscriptions", [])

        # Staff-group accounts retain their local email when Mozilla's address changes.
        if email and (email != user.email) and not profile.in_staff_group:
            if User.all_users.exclude(pk=user.pk).filter(email__iexact=email.strip()).exists():
                if request:
                    msg = _(
                        "The e-mail address used with this Mozilla account is already "
                        "linked in another profile."
                    )
                    messages.error(request, msg)
                return None
            user.email = email
            user_attr_changed = True

        profile.fxa_avatar = claims.get("avatar", "")
        products = Product.active.filter(codename__in=subscriptions)
        profile.products.set(products)
        self.update_contributor_status(profile)

        # Users can select their own display name.
        if not profile.name:
            profile.name = claims.get("displayName", "")

        if self.refresh_token:
            profile.fxa_refresh_token = self.refresh_token

        profile.is_mozilla_staff = is_mozilla_domain_email(email)

        if user_attr_changed:
            user.save()
        profile.save()

        # The task must see the committed address, never a rolled-back change.
        if user_attr_changed:
            transaction.on_commit(
                lambda user_id=user.pk, address=email: update_zendesk_identity.delay(
                    user_id, address
                ),
                robust=True,
            )

        return user

    def authenticate(self, request, **kwargs):
        """Authenticate a user based on the OIDC/oauth2 code flow."""

        # If the request has the /oidc/callback/ path then probably there is a login
        # attempt in the admin interface. In this case just return None and let
        # the OIDC backend handle this request.
        if request and request.path == django_reverse("oidc_authentication_callback"):
            return None

        return super().authenticate(request, **kwargs)
