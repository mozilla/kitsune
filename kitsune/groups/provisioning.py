import logging
from dataclasses import dataclass

import requests
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from kombu.exceptions import OperationalError
from zenpy.lib.exception import APIException, ZenpyException

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import (
    ZendeskClient,
    ZendeskProvisioningConflict,
    canonical_zendesk_id,
)
from kitsune.groups.invitations import queue_welcome_email
from kitsune.groups.membership import lock_enterprise_hierarchy
from kitsune.groups.models import EnterpriseInvitation
from kitsune.groups.onboarding import (
    get_enterprise_root,
    get_prepared_resources,
    require_onboarding_allowed,
)
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Profile

log = logging.getLogger("k.groups")

ZENDESK_PROVIDER_ERRORS = (APIException, ZenpyException, requests.RequestException)


@dataclass
class ZendeskProvisioningProgress:
    organization_id: str | None = None
    user_id: str | None = None
    action: str = "zendesk_organization"


def save_zendesk_membership_links(mapping, profile, progress):
    """Save independently validated identity links and report safe ownership conflicts."""
    failure = None
    if (
        mapping is not None
        and progress.organization_id is not None
        and mapping.zendesk_id != progress.organization_id
    ):
        mapping.zendesk_id = progress.organization_id
        try:
            with transaction.atomic():
                mapping.save(update_fields=["zendesk_id"])
        except IntegrityError:
            if not (
                ZendeskOrganization.objects.filter(zendesk_id=progress.organization_id)
                .exclude(pk=mapping.pk)
                .exists()
            ):
                raise
            failure = ("zendesk_organization", "zendesk_conflict")
    if profile is not None and progress.user_id is not None:
        if (
            Profile.all_profiles.filter(zendesk_id=progress.user_id)
            .exclude(pk=profile.pk)
            .exists()
        ):
            failure = ("zendesk_user", "account_conflict")
        elif profile.zendesk_id != progress.user_id:
            profile.zendesk_id = progress.user_id
            profile.save(update_fields=["zendesk_id"])
    return failure


def provision_zendesk_membership(
    *, client, company, mapping, profile, email, name, progress, removed_organization_ids=()
):
    """Resolve identities and replace only other SUMO-linked organization memberships.

    Track completed legs so callers can retain links when a later provider call fails.
    """
    progress.organization_id = client.ensure_organization(
        name=company.group.name,
        external_id=str(mapping.external_id),
        zendesk_id=mapping.zendesk_id,
    )
    if (
        ZendeskOrganization.objects.filter(zendesk_id=progress.organization_id)
        .exclude(pk=mapping.pk)
        .exists()
    ):
        raise ZendeskProvisioningConflict("zendesk_conflict")
    progress.action = "zendesk_user"
    user_id = client.ensure_user(
        email=email,
        name=name,
        locale=profile.locale,
        fxa_uid=profile.fxa_uid or None,
        zendesk_id=profile.zendesk_id or None,
    )
    if Profile.all_profiles.filter(zendesk_id=user_id).exclude(pk=profile.pk).exists():
        raise ZendeskProvisioningConflict("account_conflict")
    progress.user_id = user_id
    progress.action = "zendesk_membership"
    memberships = client.get_organization_memberships(user_id=user_id)
    organization_ids = set(ZendeskOrganization.objects.linked_ids())
    organization_ids.update(removed_organization_ids)
    organization_ids = {canonical_zendesk_id(value) for value in organization_ids}
    organization_ids.discard(progress.organization_id)
    client.remove_organization_memberships(
        user_id=user_id, organization_ids=organization_ids, memberships=memberships
    )
    client.ensure_organization_membership(
        user_id=user_id, organization_id=progress.organization_id, memberships=memberships
    )


def get_provisioning_resources(*, actor, invitation, for_update=False):
    """Authorize and validate prepared resources; accepted invitations have none."""
    root = get_enterprise_root()
    require_onboarding_allowed(actor, root)
    if invitation.status == EnterpriseInvitation.Status.ACCEPTED:
        return None
    return get_prepared_resources(invitation, root=root, for_update=for_update)


def provision_enterprise_invitation(
    *, actor, invitation, skip_ready=False
) -> EnterpriseInvitation:
    """Provision remotely before locking and revalidating local resources for persistence.

    With skip_ready, an invitation that is already ready is returned unchanged.
    """
    # Lock on the saved email, never on a possibly stale caller object.
    email = EnterpriseInvitation.objects.values_list("email", flat=True).get(pk=invitation.pk)
    progress = ZendeskProvisioningProgress()
    try:
        with lock_account_email(email):
            invitation = EnterpriseInvitation.objects.get(pk=invitation.pk)
            # Checked under the email gate: a request that read the invitation before another
            # run finished it must not redo setup, since a Zendesk failure would mark it failed.
            if skip_ready and invitation.status == EnterpriseInvitation.Status.READY:
                return invitation
            resources = get_provisioning_resources(actor=actor, invitation=invitation)
            if resources is None:
                return invitation
            company, mapping, user, profile = resources
            prepared_company, prepared_mapping, prepared_profile = company, mapping, profile
            prepared_user_id = user.pk
            failed_action = error_code = ""
            client = ZendeskClient(disable_cache=True, ratelimit_budget=0)
            try:
                provision_zendesk_membership(
                    client=client,
                    company=company,
                    mapping=mapping,
                    profile=profile,
                    email=invitation.email,
                    name=user.get_full_name() if invitation.created_user else profile.display_name,
                    progress=progress,
                )
            except (ZendeskProvisioningConflict, *ZENDESK_PROVIDER_ERRORS) as error:
                failed_action = progress.action
                error_code = (
                    error.code
                    if isinstance(error, ZendeskProvisioningConflict)
                    else "zendesk_unavailable"
                )
            organization_id, user_id = progress.organization_id, progress.user_id

            invitation = EnterpriseInvitation.objects.select_for_update().get(pk=invitation.pk)
            with lock_enterprise_hierarchy():
                resources = get_provisioning_resources(
                    actor=actor, invitation=invitation, for_update=True
                )
                if resources is None:
                    return invitation
                company, mapping, user, profile = resources
                # Accept only links this run resolved; any other change means stale results.
                if (
                    company.group_id != prepared_company.group_id
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
                        _(
                            "This invitation's prepared resources changed. Contact an administrator."
                        ),
                        code="account_conflict",
                    )

                if link_failure := save_zendesk_membership_links(mapping, profile, progress):
                    failed_action, error_code = link_failure
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
                    # Reruns never queue a second welcome; resend_enterprise_invitation replaces it.
                    if invitation.email_queued_at is None:
                        queue_welcome_email(invitation, company=company, user=user)
                invitation.failed_action = failed_action
                invitation.error_code = error_code
                invitation.save(
                    update_fields=["status", "failed_action", "error_code", "accepted_at"]
                )
                return invitation
    except ValidationError, PermissionDenied, Http404, EnterpriseInvitation.DoesNotExist:
        if progress.user_id is not None and progress.organization_id is not None:
            # Break tasks -> provisioning -> tasks; cleanup must survive revalidation rollback.
            from kitsune.groups.tasks import remove_stale_zendesk_memberships

            try:
                remove_stale_zendesk_memberships.delay(
                    prepared_user_id, progress.user_id, (progress.organization_id,)
                )
            except OperationalError:
                log.error("Could not queue Zendesk cleanup for invitation %s", invitation.pk)
        raise
