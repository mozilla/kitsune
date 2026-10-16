from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _lazy
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.zendesk import ZendeskClient, ZendeskProvisioningConflict
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.groups.onboarding import (
    get_enterprise_root,
    get_enterprise_support_config,
    get_prepared_resources,
    invitation_settings_valid,
    require_isolated_root,
    require_onboarding_allowed,
)
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Profile

INVITATION_SALT = "groups.enterprise-invitation"
INVITATION_ERRORS = {
    "invalid_invitation": _lazy("This invitation is not available. Contact your administrator."),
    "expired_invitation": _lazy("This invitation has expired. Contact your administrator."),
    "account_mismatch": _lazy(
        "Use the Mozilla account with the email address on this invitation."
    ),
    "account_conflict": _lazy(
        "This account cannot accept the invitation. Contact your administrator."
    ),
    "resource_missing": _lazy(
        "An account or company needed for this invitation is no longer available."
    ),
    "configuration_error": _lazy(
        "Enterprise support is not configured correctly. Contact your administrator."
    ),
    "company_conflict": _lazy("Your company access has changed. Contact your administrator."),
    "zendesk_unavailable": _lazy(
        "Enterprise support is temporarily unavailable. Please try again later."
    ),
}


def invitation_error(code) -> ValidationError:
    """Build an error that is safe to show the invitee."""
    code = code if code in INVITATION_ERRORS else "invalid_invitation"
    return ValidationError(INVITATION_ERRORS[code], code=code)


def invitation_landing_path(invitation) -> str:
    """Return the configured destination, or the enterprise product page in the account's locale."""
    if not invitation_settings_valid():
        raise invitation_error("configuration_error")
    if path := settings.ENTERPRISE_ONBOARDING_LANDING_PATH:
        return path
    profile = Profile.all_profiles.filter(user_id=invitation.user_id).first()
    if profile is None:
        raise invitation_error("resource_missing")
    try:
        product = get_enterprise_support_config().product
    except ValidationError as error:
        raise invitation_error(error.code) from None
    with translation.override(profile.locale):
        return product.get_absolute_url()


def require_open_invitation(invitation):
    if (
        not invitation.created_user
        or invitation.status != EnterpriseInvitation.Status.READY
        or invitation.expires_at is None
    ):
        raise invitation_error("invalid_invitation")
    if invitation.expires_at <= timezone.now():
        raise invitation_error("expired_invitation")


def get_invitation_resources(invitation, *, for_update=False):
    """Validate the saved company, account, and Zendesk links the invitation relies on."""
    try:
        root = get_enterprise_root()
        require_isolated_root(root)
        company, mapping, user, profile = get_prepared_resources(
            invitation, root=root, for_update=for_update
        )
    except Http404:
        raise invitation_error("resource_missing") from None
    except ValidationError as error:
        raise invitation_error(error.code) from None
    if profile.fxa_uid:
        raise invitation_error("account_conflict")
    if not GroupProfile.objects.containing(user).filter(pk=company.pk).exists():
        raise invitation_error("company_conflict")
    if not mapping.zendesk_id or not profile.zendesk_id:
        raise invitation_error("resource_missing")
    return company, mapping, user, profile


def issue_enterprise_invitation(*, actor, invitation) -> str:
    """Return a link token, starting the expiry window on first issue; sends no mail."""
    if not invitation_settings_valid():
        raise invitation_error("configuration_error")
    with transaction.atomic():
        invitation = (
            EnterpriseInvitation.objects.select_for_update().filter(pk=invitation.pk).first()
        )
        if invitation is None:
            raise invitation_error("invalid_invitation")
        with lock_enterprise_hierarchy():
            require_onboarding_allowed(actor, get_enterprise_root())
            first_issue = invitation.expires_at is None
            if first_issue:
                invitation.expires_at = timezone.now() + timedelta(
                    seconds=settings.ENTERPRISE_INVITATION_MAX_AGE
                )
            require_open_invitation(invitation)
            get_invitation_resources(invitation, for_update=True)
            if first_issue:
                invitation.save(update_fields=["expires_at"])
    return signing.dumps(
        {"invitation_id": invitation.pk, "version": invitation.token_version},
        salt=INVITATION_SALT,
    )


def load_enterprise_invitation(token, *, for_update=False) -> EnterpriseInvitation:
    """Resolve a link token to its open invitation; account checks run at issuance and claim."""
    if not token:
        raise invitation_error("invalid_invitation")
    try:
        data = signing.loads(token, salt=INVITATION_SALT)
    except signing.BadSignature:
        raise invitation_error("invalid_invitation") from None
    invitations = EnterpriseInvitation.objects.all()
    if for_update:
        invitations = invitations.select_for_update()
    invitation = invitations.filter(
        pk=data["invitation_id"], token_version=data["version"]
    ).first()
    if invitation is None:
        raise invitation_error("invalid_invitation")
    require_open_invitation(invitation)
    return invitation


def claim_enterprise_invitation(token, claims) -> User:
    """Link verified Mozilla claims to the prepared account and activate it.

    The caller's transaction must also cover its profile update so both commit together.
    """
    uid, email = claims.get("uid"), claims.get("email")
    if not (isinstance(uid, str) and uid.strip() and isinstance(email, str) and email.strip()):
        raise invitation_error("account_mismatch")
    if settings.READ_ONLY:
        raise invitation_error("configuration_error")
    with lock_account_email(email):
        invitation = load_enterprise_invitation(token)
        if email.strip().casefold() != invitation.email:
            raise invitation_error("account_mismatch")
        _, _, _, profile = get_invitation_resources(invitation)
        if Profile.all_profiles.filter(fxa_uid=uid).exists():
            raise invitation_error("account_conflict")
        try:
            ZendeskClient(disable_cache=True, ratelimit_budget=0).bind_user_identity(
                zendesk_id=profile.zendesk_id, fxa_uid=uid, email=email.strip()
            )
        except ZendeskProvisioningConflict as error:
            raise invitation_error(
                error.code if error.code in INVITATION_ERRORS else "account_conflict"
            ) from None
        except APIException, ZenpyException, requests.RequestException:
            raise invitation_error("zendesk_unavailable") from None

        # Zendesk was bound without row locks, so recheck everything once they are held.
        invitation = load_enterprise_invitation(token, for_update=True)
        with lock_enterprise_hierarchy():
            _, _, user, locked_profile = get_invitation_resources(invitation, for_update=True)
            if locked_profile.zendesk_id != profile.zendesk_id:
                raise invitation_error("account_conflict")
            locked_profile.fxa_uid = uid
            locked_profile.is_fxa_migrated = True
            # Profile sync sends the display name to Zendesk; keep the provisioned name.
            if not locked_profile.name:
                name_limit = Profile._meta.get_field("name").max_length
                locked_profile.name = user.get_full_name()[:name_limit].rstrip()
            try:
                locked_profile.save(update_fields=["fxa_uid", "is_fxa_migrated", "name"])
            except IntegrityError:
                raise invitation_error("account_conflict") from None
            user.is_active = True
            user.save(update_fields=["is_active"])
            invitation.status = EnterpriseInvitation.Status.ACCEPTED
            invitation.accepted_at = timezone.now()
            invitation.token_version += 1
            invitation.save(update_fields=["status", "accepted_at", "token_version"])
            return user
