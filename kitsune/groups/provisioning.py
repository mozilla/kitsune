import requests
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import ZendeskClient, ZendeskProvisioningConflict
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import EnterpriseInvitation
from kitsune.groups.onboarding import (
    get_enterprise_root,
    get_prepared_resources,
    require_onboarding_allowed,
)
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Profile


def get_provisioning_resources(*, actor, invitation, for_update=False):
    """Read and validate prepared resources; callers choose when to lock them."""
    root = get_enterprise_root()
    require_onboarding_allowed(actor, root)
    if invitation.status == EnterpriseInvitation.Status.ACCEPTED:
        return None
    resources = get_prepared_resources(invitation, root=root, for_update=for_update)
    if invitation.status not in (
        EnterpriseInvitation.Status.PENDING,
        EnterpriseInvitation.Status.FAILED,
        EnterpriseInvitation.Status.READY,
    ):
        raise ValidationError(
            _("This invitation's status is inconsistent. Contact an administrator."),
            code="configuration_error",
        )
    return resources


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
            if failed_action:
                invitation.status = EnterpriseInvitation.Status.FAILED
            else:
                user.groups.add(company.group)
                if invitation.created_user:
                    invitation.status = EnterpriseInvitation.Status.READY
                else:
                    # Existing accounts need no link, so the membership grant completes them.
                    invitation.status = EnterpriseInvitation.Status.ACCEPTED
                    invitation.accepted_at = timezone.now()
            invitation.failed_action = failed_action
            invitation.error_code = error_code
            invitation.save(update_fields=["status", "failed_action", "error_code", "accepted_at"])
            return invitation
