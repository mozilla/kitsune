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
from django.utils.translation import gettext as _
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskClient, ZendeskProvisioningConflict
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


def get_enterprise_support_config(*, include_live_chat=False) -> ProductSupportConfig:
    try:
        product = Product.objects.get(slug=settings.ENTERPRISE_GROUP_SLUG, is_archived=False)
        config = ProductSupportConfig.objects.select_related("zendesk_config").get(
            product=product, is_active=True, zendesk_config__isnull=False
        )
    except (
        Product.DoesNotExist,
        Product.MultipleObjectsReturned,
        ProductSupportConfig.DoesNotExist,
        ProductSupportConfig.MultipleObjectsReturned,
    ):
        raise ValidationError(
            _(
                "Ask an administrator to configure one active enterprise product with Zendesk support."
            ),
            code="configuration_error",
        ) from None

    if config.subscription_only:
        raise ValidationError(
            _(
                "Enterprise support must not require a product subscription. Contact an administrator."
            ),
            code="configuration_error",
        )
    ticket_form_id = config.zendesk_config.ticket_form_id.strip()
    if not (ticket_form_id.isascii() and ticket_form_id.isdecimal() and int(ticket_form_id) > 0):
        raise ValidationError(
            _(
                "Ask an administrator to set a valid Zendesk ticket form ID for enterprise support."
            ),
            code="configuration_error",
        )
    try:
        config.full_clean()
    except ValidationError:
        raise ValidationError(
            _("The enterprise support configuration is invalid. Contact an administrator."),
            code="configuration_error",
        ) from None

    if include_live_chat and not (
        waffle.switch_is_active("zendesk-chat")
        and settings.ZENDESK_CHAT_WIDGET_KEY
        and settings.ZENDESK_CHAT_SIGNING_KEY_ID
        and settings.ZENDESK_CHAT_SIGNING_SECRET
    ):
        raise ValidationError(
            _("Live chat is not configured. Disable live chat or contact an administrator."),
            code="configuration_error",
        )
    return config


def _require_onboarding_allowed(actor, root):
    if not can_onboard_enterprise(actor, root):
        raise PermissionDenied
    if settings.READ_ONLY:
        raise PermissionDenied(
            _("Company settings cannot be changed while the site is read-only.")
        )
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


def _require_unique_name_and_slug(name, slug):
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


def _save_support_organization(company, config, include_live_chat):
    organization = (
        SupportOrganization.objects.select_for_update()
        .filter(config=config, group=company.group)
        .first()
    )
    if organization is None:
        organization = SupportOrganization(config=config, group=company.group)
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
            and SupportOrganization.objects.filter(config=config, group=company.group).exists()
        ):
            raise ValidationError(
                _("This company's support settings changed. Reload the page and try again."),
                code="company_conflict",
            ) from None
        raise
    return organization


def _link_zendesk_organization(company, zendesk_organization_id):
    mapping, _created = ZendeskOrganization.objects.select_for_update().get_or_create(
        group_profile=company
    )
    requested_id = (zendesk_organization_id or "").strip()
    if not requested_id or requested_id == mapping.zendesk_id:
        return
    try:
        canonical_id = ZendeskClient(disable_cache=True, ratelimit_budget=0).validate_organization(
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

    if mapping.zendesk_id == canonical_id:
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


@transaction.atomic
@lock_enterprise_hierarchy(exclusive=True)
def create_enterprise_company(
    *, actor, name: str, include_live_chat: bool, zendesk_organization_id: str | None = None
) -> GroupProfile:
    root = get_enterprise_root(for_update=True)
    _require_onboarding_allowed(actor, root)
    config = get_enterprise_support_config(include_live_chat=include_live_chat)
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
    _require_unique_name_and_slug(name, slug)
    try:
        with transaction.atomic():
            group = Group.objects.create(name=name)
            company = GroupProfile.objects.add_child(
                root, create_kwargs={"group": group, "slug": slug}
            )
    except IntegrityError:
        _require_unique_name_and_slug(name, slug)
        raise
    _save_support_organization(company, config, include_live_chat)
    _link_zendesk_organization(company, zendesk_organization_id)
    return company


@transaction.atomic
@lock_enterprise_hierarchy()
def configure_enterprise_company(
    *, actor, company, include_live_chat: bool, zendesk_organization_id: str | None = None
) -> SupportOrganization:
    root = get_enterprise_root()
    _require_onboarding_allowed(actor, root)
    company = get_enterprise_company(root, pk=company.pk, for_update=True)
    config = get_enterprise_support_config(include_live_chat=include_live_chat)
    organization = _save_support_organization(company, config, include_live_chat)
    _link_zendesk_organization(company, zendesk_organization_id)
    return organization


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

    landing_path = settings.ENTERPRISE_ONBOARDING_LANDING_PATH
    invalid_landing_path = landing_path and (
        not landing_path.startswith("/")
        or landing_path.startswith("//")
        or "\\" in landing_path
        or any(ord(char) < 32 or ord(char) == 127 for char in landing_path)
    )
    if (
        invalid_landing_path
        or not isinstance(settings.ENTERPRISE_INVITATION_MAX_AGE, int)
        or settings.ENTERPRISE_INVITATION_MAX_AGE <= 0
    ):
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
            _require_onboarding_allowed(actor, root)
            company = get_enterprise_company(root, pk=company.pk, for_update=True)
            if invitation and invitation.company_id != company.pk:
                raise ValidationError(
                    _("This email already has an invitation to another company."),
                    code="company_conflict",
                )
            support = (
                SupportOrganization.objects.select_for_update()
                .filter(
                    group=company.group,
                    config__is_active=True,
                    config__product__slug=settings.ENTERPRISE_GROUP_SLUG,
                )
                .first()
            )
            config = get_enterprise_support_config(
                include_live_chat=bool(support and support.include_live_chat)
            )
            mapping = (
                ZendeskOrganization.objects.select_for_update()
                .filter(group_profile=company)
                .first()
            )
            if invitation and (
                invitation.support_config_id != config.pk or support is None or mapping is None
            ):
                raise ValidationError(
                    _(
                        "This invitation's support configuration changed. Contact an administrator."
                    ),
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
                        _(
                            "This account cannot be invited automatically. Contact an administrator."
                        ),
                        code="account_conflict",
                    )
                validate_enterprise_memberships([user.pk], [company.group_id])
                user_groups = GroupProfile.objects.containing(user)
                if (
                    user_groups.filter(group__support_organizations__config=config)
                    .exclude(group_id=company.group_id)
                    .exists()
                ):
                    raise ValidationError(
                        _("This account already belongs to another support organization."),
                        code="company_conflict",
                    )
                if invitation:
                    return invitation
                if user_groups.filter(pk=company.pk).exists():
                    accepted = (
                        EnterpriseInvitation.objects.filter(
                            company=company, user=user, status=EnterpriseInvitation.Status.ACCEPTED
                        )
                        .order_by("-accepted_at", "-pk")
                        .first()
                    )
                    if accepted:
                        return accepted

            if support is None:
                _save_support_organization(company, config, False)
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
                        support_config=config,
                        email=email,
                        user=user,
                        created_by=actor,
                        created_user=created_user,
                        completed_actions=["sumo_account"],
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
