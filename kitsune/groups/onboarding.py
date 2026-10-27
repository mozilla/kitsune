import requests
import waffle
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import (
    ZendeskClient,
    ZendeskProvisioningConflict,
    canonical_zendesk_id,
)
from kitsune.groups.membership import lock_enterprise_hierarchy, validate_enterprise_memberships
from kitsune.groups.models import EnterpriseInvitation, GroupProfile
from kitsune.products.models import Product, ProductSupportConfig, SupportOrganization
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Profile
from kitsune.users.utils import normalize_username, suggest_username


def get_enterprise_root(*, for_update=False) -> GroupProfile:
    profiles = GroupProfile.objects.select_related("group")
    if for_update:
        profiles = profiles.select_for_update(of=("self",))
    try:
        return profiles.get(slug=settings.ENTERPRISE_GROUP_SLUG, depth=1)
    except GroupProfile.DoesNotExist, GroupProfile.MultipleObjectsReturned:
        raise ValidationError(
            _("Ask an administrator to configure an existing top-level enterprise group."),
            code="configuration_error",
        ) from None


def can_onboard_enterprise(user, root) -> bool:
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.is_staff
        and root.can_moderate_group(user)
    )


def get_enterprise_company(root, *, viewer=None, for_update=False, **lookup) -> GroupProfile:
    """Resolve a direct company child, optionally filtering by the viewer's visibility."""
    if root.depth != 1:
        raise Http404
    profiles = GroupProfile.objects.select_related("group").filter(
        depth=2, path__startswith=root.path
    )
    if viewer is not None:
        # Keep DISTINCT in the visibility subquery so the outer query can lock rows.
        profiles = profiles.filter(pk__in=GroupProfile.objects.visible(viewer).values("pk"))
    if for_update:
        profiles = profiles.select_for_update(of=("self",))
    return get_object_or_404(profiles, **lookup)


def get_live_chat_config() -> ProductSupportConfig:
    """Return the enterprise product's support configuration, which carries company live chat."""
    products = list(
        Product.objects.filter(slug=settings.ENTERPRISE_GROUP_SLUG, is_archived=False)[:2]
    )
    config = ProductSupportConfig.objects.active_for(products[0]) if len(products) == 1 else None
    # Chat eligibility applies the subscription gate, so a subscription-only config hides chat.
    if (
        config is None
        or config.zendesk_config_id is None
        or config.subscription_only
        or not (
            waffle.switch_is_active("zendesk-chat")
            and settings.ZENDESK_CHAT_WIDGET_KEY
            and settings.ZENDESK_CHAT_SIGNING_KEY_ID
            and settings.ZENDESK_CHAT_SIGNING_SECRET
        )
    ):
        raise ValidationError(
            _("Live chat is not configured. Disable live chat or contact an administrator."),
            code="configuration_error",
        )
    return config


def require_onboarding_allowed(actor, root):
    actor = (
        User.all_users.filter(pk=actor.pk).first() if actor and actor.is_authenticated else None
    )
    if not can_onboard_enterprise(actor, root):
        raise PermissionDenied
    if settings.READ_ONLY:
        raise PermissionDenied(
            _("Company settings cannot be changed while the site is read-only.")
        )
    require_isolated_root(root)


def require_isolated_root(root):
    if (
        root.visibility
        not in (
            GroupProfile.Visibility.PRIVATE,
            GroupProfile.Visibility.MODERATED,
        )
        or not root.isolation_enabled
    ):
        raise ValidationError(
            _(
                "The enterprise group must be private or moderated with sibling isolation enabled. "
                "Contact an administrator."
            ),
            code="configuration_error",
        )


def invitation_settings_valid() -> bool:
    """Whether the landing path is blank or a local path, and the link lifetime is positive."""
    path = settings.ENTERPRISE_ONBOARDING_LANDING_PATH
    max_age = settings.ENTERPRISE_INVITATION_MAX_AGE
    return (
        isinstance(path, str)
        and (
            not path
            or (
                path.startswith("/")
                and "\\" not in path
                and path.isprintable()
                and url_has_allowed_host_and_scheme(path, allowed_hosts=None)
            )
        )
        and type(max_age) is int
        and max_age > 0
    )


def require_invitation_account(*, user, profile, company, invitation=None):
    """Check account eligibility and company ownership without changing the account."""
    if (
        profile is None
        or profile.account_type != Profile.AccountType.REGULAR
        or user.is_staff
        or user.is_superuser
    ):
        eligible = False
    elif (
        invitation
        and invitation.created_user
        and invitation.accepted_at is None
        and not profile.fxa_uid
    ):
        # A prepared account is reusable only while it remains unused and unclaimed.
        eligible = not (
            user.is_active
            or user.has_usable_password()
            or profile.is_fxa_migrated
            or user.last_login is not None
        )
    else:
        eligible = user.is_active and bool(profile.fxa_uid)
    if not eligible:
        raise ValidationError(
            _("This account cannot be invited automatically. Contact an administrator."),
            code="account_conflict",
        )
    validate_enterprise_memberships([user.pk], [company.group_id])


def get_prepared_resources(invitation, *, root, for_update=False):
    """Validate saved company and account resources before I/O or under final locks."""
    if invitation.user_id is None:
        raise ValidationError(
            _("The account prepared for this invitation no longer exists."),
            code="resource_missing",
        )
    company = get_enterprise_company(root, pk=invitation.company_id, for_update=for_update)
    mappings = ZendeskOrganization.objects.all()
    users = User.all_users.all()
    profiles = Profile.all_profiles.all()
    if for_update:
        mappings = mappings.select_for_update()
        users = users.select_for_update()
        profiles = profiles.select_for_update()
    mapping = mappings.filter(group_profile=company).first()
    if mapping is None:
        raise ValidationError(
            _("A resource prepared for this invitation no longer exists."),
            code="resource_missing",
        )
    users = list(users.filter(email__iexact=invitation.email).order_by("pk")[:2])
    if len(users) != 1 or users[0].pk != invitation.user_id:
        raise ValidationError(
            _("This email cannot be provisioned automatically. Contact an administrator."),
            code="account_conflict",
        )
    user = users[0]
    profile = profiles.filter(user=user).first()
    if profile is None:
        raise ValidationError(
            _("The account profile prepared for this invitation no longer exists."),
            code="resource_missing",
        )
    require_invitation_account(user=user, profile=profile, company=company, invitation=invitation)
    try:
        if mapping.zendesk_id:
            canonical_zendesk_id(mapping.zendesk_id)
        remote_id = canonical_zendesk_id(profile.zendesk_id) if profile.zendesk_id else None
    except ZendeskProvisioningConflict:
        raise ValidationError(
            _("A provisioned Zendesk resource has an invalid ID. Contact an administrator."),
            code="configuration_error",
        ) from None
    if (
        remote_id
        and Profile.all_profiles.filter(zendesk_id=remote_id).exclude(pk=profile.pk).exists()
    ):
        raise ValidationError(
            _("This Zendesk account cannot be linked automatically. Contact an administrator."),
            code="account_conflict",
        )
    user.profile = profile
    return company, mapping, user, profile


def require_unique_company_identity(name, slug):
    if Group.objects.filter(name__iexact=name).exists():
        raise ValidationError(
            {
                "name": ValidationError(
                    _("A group with this company name already exists. Choose a different name."),
                    code="company_conflict",
                )
            }
        )
    if GroupProfile.objects.filter(slug=slug).exists():
        raise ValidationError(
            {
                "name": ValidationError(
                    _("A group with this company URL already exists. Choose a different name."),
                    code="company_conflict",
                )
            }
        )


def save_live_chat(company, include_live_chat):
    """Record the company's live chat choice; turning chat off never creates an organization."""
    organizations = SupportOrganization.objects.select_for_update(of=("self",)).filter(
        group=company.group
    )
    if include_live_chat:
        config = get_live_chat_config()
        organizations = [
            organizations.filter(config=config).first()
            or SupportOrganization(config=config, group=company.group)
        ]
    else:
        organizations = organizations.filter(
            config__product__slug=settings.ENTERPRISE_GROUP_SLUG, include_live_chat=True
        )
    for organization in organizations:
        organization.include_live_chat = include_live_chat
        try:
            organization.full_clean()
        except ValidationError:
            raise ValidationError(
                _(
                    "These support settings conflict with the existing organization configuration. "
                    "Contact an administrator."
                ),
                code="configuration_error",
            ) from None
        try:
            with transaction.atomic():
                organization.save()
        except IntegrityError:
            if (
                organization.pk is None
                and SupportOrganization.objects.filter(
                    config=organization.config, group=company.group
                ).exists()
            ):
                raise ValidationError(
                    _("This company's support settings changed. Reload the page and try again."),
                    code="company_conflict",
                ) from None
            raise


def validate_zendesk_organization_id(zendesk_organization_id, *, company=None):
    requested_id = (zendesk_organization_id or "").strip()
    if not requested_id:
        return None
    if (
        company is not None
        and ZendeskOrganization.objects.filter(
            group_profile=company, zendesk_id=requested_id
        ).exists()
    ):
        return requested_id
    try:
        return ZendeskClient(disable_cache=True, ratelimit_budget=0).validate_organization(
            requested_id
        )
    except ZendeskProvisioningConflict as error:
        raise ValidationError(
            {
                "zendesk_organization_id": ValidationError(
                    _(
                        "The Zendesk organization could not be linked. "
                        "Check the organization ID or contact an administrator."
                    ),
                    code=error.code,
                )
            }
        ) from None
    except APIException, ZenpyException, requests.RequestException:
        raise ValidationError(
            {
                "zendesk_organization_id": ValidationError(
                    _(
                        "Zendesk could not verify this organization. "
                        "Try again or ask an administrator to check the connection."
                    ),
                    code="zendesk_unavailable",
                )
            }
        ) from None


def link_zendesk_organization(company, canonical_id):
    mapping, _created = ZendeskOrganization.objects.select_for_update().get_or_create(
        group_profile=company
    )
    if not canonical_id or mapping.zendesk_id == canonical_id:
        return
    if mapping.zendesk_id:
        raise ValidationError(
            {
                "zendesk_organization_id": ValidationError(
                    _(
                        "This company is already linked to a Zendesk organization and cannot be reassigned."
                    ),
                    code="company_conflict",
                )
            }
        )
    mapping.zendesk_id = canonical_id
    try:
        with transaction.atomic():
            mapping.save(update_fields=["zendesk_id"])
    except IntegrityError:
        conflicts = ZendeskOrganization.objects.filter(zendesk_id=canonical_id).exclude(
            pk=mapping.pk
        )
        if conflicts.exists():
            raise ValidationError(
                {
                    "zendesk_organization_id": ValidationError(
                        _("This Zendesk organization is already linked to another company."),
                        code="company_conflict",
                    )
                }
            ) from None
        raise


def create_enterprise_company(
    *, actor, name: str, include_live_chat: bool, zendesk_organization_id: str | None = None
) -> GroupProfile:
    root = get_enterprise_root()
    require_onboarding_allowed(actor, root)
    if include_live_chat:
        get_live_chat_config()
    name = name.strip()
    if not name or len(name) > Group._meta.get_field("name").max_length:
        raise ValidationError(
            {
                "name": ValidationError(
                    _("Enter a company name within the allowed length."), code="invalid"
                )
            }
        )
    slug = slugify(name)
    if not slug or len(slug) > GroupProfile._meta.get_field("slug").max_length:
        raise ValidationError(
            {
                "name": ValidationError(
                    _(
                        "Choose a company name that produces a nonempty URL slug of at most 80 characters."
                    ),
                    code="invalid",
                )
            }
        )
    require_unique_company_identity(name, slug)
    canonical_id = validate_zendesk_organization_id(zendesk_organization_id)

    # Recheck mutable prerequisites after the remote lookup, before any writes.
    with lock_enterprise_hierarchy(exclusive=True):
        root = get_enterprise_root(for_update=True)
        require_onboarding_allowed(actor, root)
        require_unique_company_identity(name, slug)
        try:
            with transaction.atomic():
                group = Group.objects.create(name=name)
                company = GroupProfile.objects.add_child(
                    root, create_kwargs={"group": group, "slug": slug}
                )
        except IntegrityError:
            require_unique_company_identity(name, slug)
            raise
        save_live_chat(company, include_live_chat)
        link_zendesk_organization(company, canonical_id)
        return company


def configure_enterprise_company(
    *, actor, company, include_live_chat: bool, zendesk_organization_id: str | None = None
):
    root = get_enterprise_root()
    require_onboarding_allowed(actor, root)
    company = get_enterprise_company(root, pk=company.pk)
    if include_live_chat:
        get_live_chat_config()
    canonical_id = validate_zendesk_organization_id(zendesk_organization_id, company=company)

    with lock_enterprise_hierarchy():
        root = get_enterprise_root()
        require_onboarding_allowed(actor, root)
        company = get_enterprise_company(root, pk=company.pk, for_update=True)
        save_live_chat(company, include_live_chat)
        link_zendesk_organization(company, canonical_id)


def invite_enterprise_user(
    *, actor, company, email: str, first_name: str, last_name: str
) -> EnterpriseInvitation:
    email = email.strip().casefold()
    first_name, last_name = first_name.strip(), last_name.strip()
    try:
        validate_email(email)
        if len(email) > 254:
            raise ValidationError(_("Enter a valid email address."), code="invalid")
    except ValidationError as error:
        raise ValidationError({"email": error}) from None
    for field, value in (("first_name", first_name), ("last_name", last_name)):
        if not value or len(value) > User._meta.get_field(field).max_length:
            raise ValidationError(
                {
                    field: ValidationError(
                        _("Enter a name within the allowed length."), code="invalid"
                    )
                }
            )

    if not invitation_settings_valid():
        raise ValidationError(
            _(
                "Ask an administrator to configure a valid enterprise invitation destination and expiry."
            ),
            code="configuration_error",
        )

    with lock_account_email(email):
        invitation = (
            EnterpriseInvitation.objects.select_for_update()
            .filter(email__iexact=email)
            .exclude(status=EnterpriseInvitation.Status.ACCEPTED)
            .first()
        )
        with lock_enterprise_hierarchy():
            root = get_enterprise_root()
            require_onboarding_allowed(actor, root)
            company = get_enterprise_company(root, pk=company.pk, for_update=True)
            if invitation and invitation.company_id != company.pk:
                raise ValidationError(
                    _("This email already has an invitation to another company."),
                    code="company_conflict",
                )
            mapping = (
                ZendeskOrganization.objects.select_for_update()
                .filter(group_profile=company)
                .first()
            )
            if invitation and mapping is None:
                raise ValidationError(
                    _("This company's support settings are incomplete. Contact an administrator."),
                    code="configuration_error",
                )
            if invitation and invitation.user_id is None:
                raise ValidationError(
                    _("The account prepared for this invitation no longer exists."),
                    code="resource_missing",
                )

            users = list(
                User.all_users.select_for_update().filter(email__iexact=email).order_by("pk")[:2]
            )
            if len(users) > 1 or (invitation and (not users or users[0].pk != invitation.user_id)):
                raise ValidationError(
                    _(
                        "This email cannot be invited automatically. Ask an administrator to resolve the account."
                    ),
                    code="account_conflict",
                )
            user = users[0] if users else None
            if user is not None:
                profile = Profile.all_profiles.select_for_update().filter(user=user).first()
                require_invitation_account(
                    user=user, profile=profile, company=company, invitation=invitation
                )
                if invitation:
                    return invitation
                if GroupProfile.objects.containing(user).filter(pk=company.pk).exists():
                    accepted = (
                        EnterpriseInvitation.objects.filter(
                            company=company, user=user, status=EnterpriseInvitation.Status.ACCEPTED
                        )
                        .order_by("-accepted_at", "-pk")
                        .first()
                    )
                    if accepted:
                        return accepted

            if mapping is None:
                ZendeskOrganization.objects.create(group_profile=company)

            created_user = user is None
            if created_user:
                username_email = (
                    email
                    if normalize_username(email.split("@", 1)[0])
                    else "enterprise-user@example.invalid"
                )
                while True:
                    username = suggest_username(username_email)
                    user = User(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=False,
                    )
                    user.set_unusable_password()
                    try:
                        with transaction.atomic():
                            user.save(force_insert=True)
                            Profile.objects.create(
                                user=user,
                                account_type=Profile.AccountType.REGULAR,
                                name="",
                                public_email=False,
                                is_fxa_migrated=False,
                                fxa_uid=None,
                            )
                    except IntegrityError:
                        if User.all_users.filter(username=username).exists():
                            continue
                        raise
                    break

            try:
                with transaction.atomic():
                    return EnterpriseInvitation.objects.create(
                        company=company,
                        email=email,
                        user=user,
                        created_by=actor,
                        created_user=created_user,
                    )
            except IntegrityError:
                if (
                    EnterpriseInvitation.objects.filter(email__iexact=email)
                    .exclude(status=EnterpriseInvitation.Status.ACCEPTED)
                    .exists()
                ):
                    raise ValidationError(
                        _("This email already has an unfinished enterprise invitation."),
                        code="company_conflict",
                    ) from None
                raise
