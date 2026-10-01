import requests
import waffle
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskClient, ZendeskProvisioningConflict
from kitsune.groups.models import GroupProfile
from kitsune.products.models import Product, ProductSupportConfig, SupportOrganization


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
    profiles = (
        GroupProfile.objects.visible(viewer) if viewer is not None else GroupProfile.objects.all()
    )
    profiles = profiles.select_related("group").filter(depth=2, path__startswith=root.path)
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
