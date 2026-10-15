import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskClient, ZendeskProvisioningConflict
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import EnterpriseInvitation
from kitsune.groups.onboarding import (
    get_enterprise_company,
    get_enterprise_root,
    get_enterprise_support_config,
    require_invitation_account,
    require_onboarding_allowed,
)
from kitsune.products.models import SupportOrganization
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Profile


def get_provisioning_resources(*, actor, invitation, for_update=False):
    """Read and validate prepared resources; callers choose when to lock them."""
    root = get_enterprise_root()
    require_onboarding_allowed(actor, root)
    if invitation.status == EnterpriseInvitation.Status.ACCEPTED:
        return None
    if invitation.user_id is None:
        raise ValidationError(
            _("The account prepared for this invitation no longer exists."),
            code="resource_missing",
        )
    company = get_enterprise_company(root, pk=invitation.company_id, for_update=for_update)
    supports = SupportOrganization.objects.all()
    mappings = ZendeskOrganization.objects.all()
    users = User.all_users.all()
    profiles = Profile.all_profiles.all()
    if for_update:
        supports = supports.select_for_update()
        mappings = mappings.select_for_update()
        users = users.select_for_update()
        profiles = profiles.select_for_update()
    support = supports.filter(
        group_id=company.group_id,
        config__is_active=True,
        config__product__slug=settings.ENTERPRISE_GROUP_SLUG,
    ).first()
    config = get_enterprise_support_config(
        include_live_chat=bool(support and support.include_live_chat)
    )
    if support is None or support.config_id != config.pk:
        raise ValidationError(
            _("This company's support settings are incomplete. Contact an administrator."),
            code="configuration_error",
        )
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
    require_invitation_account(
        user=user,
        profile=profile,
        company=company,
        config=config,
        invitation=invitation,
    )
    if invitation.status not in (
        EnterpriseInvitation.Status.PENDING,
        EnterpriseInvitation.Status.FAILED,
        EnterpriseInvitation.Status.READY,
    ):
        raise ValidationError(
            _("This invitation's status is inconsistent. Contact an administrator."),
            code="configuration_error",
        )
    for zendesk_id in (mapping.zendesk_id, profile.zendesk_id):
        if zendesk_id and not (
            zendesk_id.isascii() and zendesk_id.isdecimal() and int(zendesk_id) > 0
        ):
            raise ValidationError(
                _("A provisioned Zendesk resource has an invalid ID. Contact an administrator."),
                code="configuration_error",
            )
    if (
        profile.zendesk_id
        and Profile.all_profiles.filter(zendesk_id=str(int(profile.zendesk_id)))
        .exclude(pk=profile.pk)
        .exists()
    ):
        raise ValidationError(
            _("This Zendesk account cannot be linked automatically. Contact an administrator."),
            code="account_conflict",
        )
    return company, mapping, user, profile


def provision_enterprise_invitation(*, actor, invitation) -> EnterpriseInvitation:
    """Provision remotely before locking and revalidating local resources for persistence."""
    email = EnterpriseInvitation.objects.values_list("email", flat=True).get(pk=invitation.pk)
    with lock_account_email(email):
        invitation = EnterpriseInvitation.objects.get(pk=invitation.pk)
        if invitation.email != email:
            raise ValidationError(
                _("This invitation's email changed. Contact an administrator."),
                code="account_conflict",
            )
        resources = get_provisioning_resources(actor=actor, invitation=invitation)
        if resources is None:
            return invitation
        company, mapping, user, profile = resources
        prepared_invitation = invitation
        prepared_company, prepared_mapping, prepared_profile = company, mapping, profile
        organization_id = user_id = None
        failed_action = error_code = ""
        client = ZendeskClient(disable_cache=True, ratelimit_budget=0)
        try:
            action = "zendesk_organization"
            organization_id = client.ensure_organization(
                name=company.group.name,
                external_id=str(mapping.external_id),
                zendesk_id=mapping.zendesk_id,
            )
            if (
                ZendeskOrganization.objects.filter(zendesk_id=organization_id)
                .exclude(pk=mapping.pk)
                .exists()
            ):
                raise ZendeskProvisioningConflict("zendesk_conflict")
            action = "zendesk_user"
            remote_user_id = client.ensure_user(
                email=invitation.email,
                name=user.get_full_name() if invitation.created_user else profile.display_name,
                locale=profile.locale,
                fxa_uid=profile.fxa_uid or None,
                zendesk_id=profile.zendesk_id or None,
            )
            if (
                Profile.all_profiles.filter(zendesk_id=remote_user_id)
                .exclude(pk=profile.pk)
                .exists()
            ):
                raise ZendeskProvisioningConflict("account_conflict")
            user_id = remote_user_id
            action = "zendesk_membership"
            client.ensure_organization_membership(user_id=user_id, organization_id=organization_id)
        except (
            ZendeskProvisioningConflict,
            APIException,
            ZenpyException,
            requests.RequestException,
        ) as error:
            failed_action = action
            error_code = (
                error.code
                if isinstance(error, ZendeskProvisioningConflict)
                else "zendesk_unavailable"
            )

        invitation = EnterpriseInvitation.objects.select_for_update().get(pk=invitation.pk)
        with lock_enterprise_hierarchy():
            resources = get_provisioning_resources(
                actor=actor, invitation=invitation, for_update=True
            )
            if resources is None:
                return invitation
            company, mapping, user, profile = resources
            if (
                invitation.email != prepared_invitation.email
                or invitation.company_id != prepared_invitation.company_id
                or invitation.user_id != prepared_invitation.user_id
                or company.group_id != prepared_company.group_id
                or mapping.pk != prepared_mapping.pk
                or mapping.external_id != prepared_mapping.external_id
                or (
                    mapping.zendesk_id != prepared_mapping.zendesk_id
                    and (organization_id is None or mapping.zendesk_id != organization_id)
                )
                or profile.pk != prepared_profile.pk
                or profile.fxa_uid != prepared_profile.fxa_uid
                or (
                    profile.zendesk_id != prepared_profile.zendesk_id
                    and (user_id is None or profile.zendesk_id != user_id)
                )
            ):
                raise ValidationError(
                    _("This invitation's prepared resources changed. Contact an administrator."),
                    code="account_conflict",
                )

            if organization_id is not None and mapping.zendesk_id != organization_id:
                mapping.zendesk_id = organization_id
                try:
                    with transaction.atomic():
                        mapping.save(update_fields=["zendesk_id"])
                except IntegrityError:
                    if not (
                        ZendeskOrganization.objects.filter(zendesk_id=organization_id)
                        .exclude(pk=mapping.pk)
                        .exists()
                    ):
                        raise
                    failed_action, error_code = "zendesk_organization", "zendesk_conflict"
            if user_id is not None:
                if Profile.all_profiles.filter(zendesk_id=user_id).exclude(pk=profile.pk).exists():
                    failed_action, error_code = "zendesk_user", "account_conflict"
                elif profile.zendesk_id != user_id:
                    profile.zendesk_id = user_id
                    profile.save(update_fields=["zendesk_id"])
            invitation.status = (
                EnterpriseInvitation.Status.FAILED
                if failed_action
                else EnterpriseInvitation.Status.READY
            )
            invitation.failed_action = failed_action
            invitation.error_code = error_code
            invitation.save(update_fields=["status", "failed_action", "error_code"])
            return invitation
