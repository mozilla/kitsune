from datetime import timedelta
from email.utils import make_msgid

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import pgettext
from post_office.models import PRIORITY, STATUS, Email
from post_office.settings import get_message_id_enabled, get_message_id_fqdn
from post_office.tasks import send_queued_mail

from kitsune.customercare.zendesk import ZendeskClient, ZendeskProvisioningConflict
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.groups.onboarding import (
    ZENDESK_PROVIDER_ERRORS,
    get_enterprise_root,
    get_prepared_resources,
    invitation_settings_valid,
    require_isolated_root,
    require_onboarding_allowed,
)
from kitsune.products.models import SupportCoverage
from kitsune.products.routing import chat_unavailable_reason
from kitsune.products.utils import get_covered_products
from kitsune.sumo.email_utils import make_mail, safe_translation
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
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
    """Return the configured destination, or the company page in the account's locale."""
    if not invitation_settings_valid():
        raise invitation_error("configuration_error")
    if path := settings.ENTERPRISE_ONBOARDING_LANDING_PATH:
        return path
    profile = Profile.all_profiles.filter(user_id=invitation.user_id).first()
    if profile is None:
        raise invitation_error("resource_missing")
    with translation.override(profile.locale):
        return invitation.company.get_absolute_url()


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


def invitation_token(invitation) -> str:
    return signing.dumps(
        {"invitation_id": invitation.pk, "version": invitation.token_version},
        salt=INVITATION_SALT,
    )


def queue_welcome_email(invitation, *, company, user):
    """Queue the welcome for delivery after commit and record it on the invitation.

    New accounts get the secure first-login link with a fresh expiry. Existing accounts are
    already accepted, so they get a Mozilla sign-in link that continues to the landing page.
    """
    if not invitation_settings_valid():
        raise invitation_error("configuration_error")
    if invitation.created_user:
        invitation.expires_at = timezone.now() + timedelta(
            seconds=settings.ENTERPRISE_INVITATION_MAX_AGE
        )
        start_path = None
    else:
        # Company pages are private, so a signed-out invitee must sign in first.
        start_path = urlparams(
            reverse("users.fxa_authentication_init"), next=invitation_landing_path(invitation)
        )
    covered_products = get_covered_products(company)
    # Promise chat only while the site can deliver it; membership never depends on chat.
    includes_chat = (
        chat_unavailable_reason() is None
        and SupportCoverage.objects.effective(company)
        .filter(product__in=covered_products, includes_chat=True)
        .exists()
    )
    host = Site.objects.get_current().domain

    @safe_translation
    def make_welcome(locale):
        # Reversed inside the locale override so the link carries the recipient's locale.
        path = start_path or reverse("groups.invitation_link", args=[invitation_token(invitation)])
        company_name = company.group.name
        return make_mail(
            subject=_("Your Mozilla Support access through {company} is ready").format(
                company=company_name
            ),
            text_template="groups/email/enterprise_invitation.ltxt",
            html_template="groups/email/enterprise_invitation.html",
            context_vars={
                "name": user.first_name or user.profile.display_name,
                "company": company_name,
                "email": invitation.email,
                "new_account": invitation.created_user,
                "covered_products": ", ".join(
                    pgettext("DB: products.Product.title", product.title)
                    for product in covered_products
                ),
                "includes_chat": includes_chat,
                "start_url": f"https://{host}{path}",
            },
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=invitation.email,
        )

    message = make_welcome(user.profile.locale)
    # Built directly: post_office's helpers would render this text as a Django template.
    email = Email(
        from_email=message.from_email,
        to=message.to,
        subject=message.subject,
        message=message.body,
        html_message=next(
            (content for content, mimetype in message.alternatives if mimetype == "text/html"),
            "",
        ),
        headers=message.extra_headers,
        priority=PRIORITY.medium,
        status=STATUS.queued,
        # A queued welcome must not deliver a link that has already expired.
        expires_at=invitation.expires_at if invitation.created_user else None,
        message_id=make_msgid(domain=get_message_id_fqdn()) if get_message_id_enabled() else None,
    )
    email.save()
    invitation.welcome_email = email
    invitation.email_queued_at = timezone.now()
    invitation.save(update_fields=["expires_at", "welcome_email", "email_queued_at"])
    # The scheduled queue run delivers it if publishing fails.
    transaction.on_commit(send_queued_mail.delay, robust=True)


def resend_enterprise_invitation(*, actor, invitation) -> EnterpriseInvitation:
    """Queue a replacement welcome with a renewed link; every earlier link stops working."""
    with transaction.atomic():
        invitation = (
            EnterpriseInvitation.objects.select_for_update().filter(pk=invitation.pk).first()
        )
        if invitation is None:
            raise invitation_error("invalid_invitation")
        with lock_enterprise_hierarchy():
            require_onboarding_allowed(actor, get_enterprise_root())
            if (
                not invitation.created_user
                or invitation.status != EnterpriseInvitation.Status.READY
            ):
                raise invitation_error("invalid_invitation")
            company, _mapping, user, _profile = get_invitation_resources(
                invitation, for_update=True
            )
            invitation.token_version += 1
            invitation.save(update_fields=["token_version"])
            if invitation.welcome_email_id:
                # Clear any retry schedule too: post-office rejects a schedule after expiry.
                Email.objects.filter(pk=invitation.welcome_email_id).exclude(
                    status=STATUS.sent
                ).update(expires_at=timezone.now(), scheduled_time=None)
            queue_welcome_email(invitation, company=company, user=user)
    return invitation


def load_enterprise_invitation(token, *, for_update=False) -> EnterpriseInvitation:
    """Resolve a link token to its open invitation; account checks run when sending and claiming."""
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
        except ZENDESK_PROVIDER_ERRORS:
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
