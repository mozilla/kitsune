import logging
from contextlib import nullcontext
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Q, Subquery
from django.utils import timezone

from kitsune.customercare.models import ZendeskOrganization
from kitsune.customercare.zendesk import (
    ZendeskClient,
    ZendeskProvisioningConflict,
    canonical_zendesk_id,
)
from kitsune.groups.membership import (
    company_organization_ids,
    enterprise_profiles,
    lock_enterprise_hierarchy,
    queue_enterprise_zendesk_sync,
)
from kitsune.groups.models import GroupProfile
from kitsune.groups.provisioning import (
    ZENDESK_PROVIDER_ERRORS,
    ZendeskProvisioningProgress,
    provision_zendesk_membership,
    save_zendesk_membership_links,
)
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.users.identity import lock_account_email
from kitsune.users.models import Deactivation, Profile

log = logging.getLogger("k.task")


class ZendeskMembershipChanged(Exception):
    """Local membership or identity changed while Zendesk was being contacted."""


class ZendeskUnavailable(Exception):
    """A provider failure reduced to its class and HTTP status; messages can contain emails."""

    @classmethod
    def from_error(cls, error):
        status = getattr(getattr(error, "response", None), "status_code", None)
        return cls(type(error).__name__, status)


RETRYABLE_ERRORS = (ZendeskUnavailable, ZendeskMembershipChanged)


def get_sync_company(user, *, for_update=False):
    """Resolve one company without choosing between ambiguous legacy memberships."""
    companies = GroupProfile.objects.enterprise_companies(user).select_related("group")
    if for_update:
        companies = companies.select_for_update(of=("self",))
    matches = list(companies[:2])
    if len(matches) > 1:
        raise ZendeskProvisioningConflict("company_conflict")
    return matches[0] if matches else None


def prepare_zendesk_company(user):
    """Commit a stable organization UUID before any provider call can use it."""
    with lock_enterprise_hierarchy():
        company = get_sync_company(user, for_update=True)
        if company is not None:
            ZendeskOrganization.objects.get_or_create(group_profile=company)


def save_current_zendesk_membership(user, company, mapping, profile, progress):
    """Keep safe identity links even if changed membership requires another sync."""
    User = get_user_model()
    with lock_enterprise_hierarchy():
        failure = None
        current_mapping = None
        if company is not None:
            locked_company = GroupProfile.objects.select_for_update().filter(pk=company.pk).first()
            current_mapping = (
                ZendeskOrganization.objects.select_for_update()
                .filter(pk=mapping.pk, group_profile=locked_company)
                .first()
            )
            if (
                locked_company is None
                or locked_company.group_id != company.group_id
                or current_mapping is None
                or current_mapping.external_id != mapping.external_id
                or current_mapping.zendesk_id not in (mapping.zendesk_id, progress.organization_id)
            ):
                current_mapping = None
                failure = ZendeskMembershipChanged("Company Zendesk identity changed")
        current_user = User.all_users.select_for_update().filter(pk=user.pk).first()
        current_profile = Profile.all_profiles.select_for_update().filter(user_id=user.pk).first()
        if (
            current_user is None
            or current_user.email.strip().casefold() != user.email.strip().casefold()
            or current_profile is None
            or current_profile.pk != profile.pk
            or current_profile.fxa_uid != profile.fxa_uid
            or current_profile.zendesk_id not in (profile.zendesk_id, progress.user_id)
        ):
            current_profile = None
            failure = ZendeskMembershipChanged("Account Zendesk identity changed")
        try:
            current_company = get_sync_company(user)
        except ZendeskProvisioningConflict as error:
            failure = error
        else:
            if (current_company.pk if current_company else None) != (
                company.pk if company else None
            ):
                failure = ZendeskMembershipChanged("Company membership changed")
        if link_failure := save_zendesk_membership_links(
            current_mapping, current_profile, progress
        ):
            failure = ZendeskProvisioningConflict(link_failure[1])
        if (
            progress.user_id is not None
            and progress.organization_id is not None
            and (current_mapping is None or current_profile is None)
        ):
            cleanup_args = (user.pk, progress.user_id, (progress.organization_id,))
            transaction.on_commit(
                lambda: remove_stale_zendesk_memberships.delay(*cleanup_args),
                robust=True,
            )
        return failure


def remove_zendesk_company_memberships(client, *, user_id, zendesk_user_id, organization_ids):
    """Remove organization memberships from a Zendesk user that no other profile owns."""
    if Profile.all_profiles.filter(zendesk_id=zendesk_user_id).exclude(user_id=user_id).exists():
        raise ZendeskProvisioningConflict("account_conflict")
    remote_id = client.validate_removal_user(zendesk_user_id)
    client.remove_organization_memberships(user_id=remote_id, organization_ids=organization_ids)


@shared_task(
    acks_late=True,
    autoretry_for=RETRYABLE_ERRORS,
    retry_backoff=2,
    retry_kwargs={"max_retries": 3},
)
@skip_if_read_only_mode
def sync_enterprise_zendesk_membership(user_id, removed_organization_ids=()):
    """Converge on current membership; return a safe failure code or None on success."""
    User = get_user_model()
    user = User.all_users.filter(pk=user_id).first()
    if user is None:
        return "user_missing"
    failure = None
    try:
        prepare_zendesk_company(user)
        email = user.email.strip().casefold()
        with lock_account_email(email):
            user = User.all_users.filter(pk=user_id).first()
            if user is None:
                return "user_missing"
            if user.email.strip().casefold() != email:
                raise ZendeskMembershipChanged("Account email changed")
            company = get_sync_company(user)
            mapping = None
            if company is not None:
                mapping = ZendeskOrganization.objects.filter(group_profile=company).first()
                if mapping is None:
                    raise ZendeskMembershipChanged("Company Zendesk mapping changed")
            profile = Profile.all_profiles.filter(user_id=user_id).first()
            if profile is None:
                return "profile_missing"
            client = ZendeskClient(disable_cache=True, ratelimit_budget=0)
            progress = ZendeskProvisioningProgress()
            try:
                if company is not None:
                    provision_zendesk_membership(
                        client=client,
                        company=company,
                        mapping=mapping,
                        profile=profile,
                        email=user.email,
                        name=profile.display_name,
                        progress=progress,
                        removed_organization_ids=removed_organization_ids,
                    )
                elif profile.zendesk_id:
                    remove_zendesk_company_memberships(
                        client,
                        user_id=user_id,
                        zendesk_user_id=profile.zendesk_id,
                        organization_ids={
                            *ZendeskOrganization.objects.linked_ids(),
                            *removed_organization_ids,
                        },
                    )
            except ZendeskProvisioningConflict as error:
                failure = error
            except ZENDESK_PROVIDER_ERRORS as error:
                failure = ZendeskUnavailable.from_error(error)
                log.warning("Zendesk unavailable for user %s: %s %s", user_id, *failure.args)
            failure = (
                save_current_zendesk_membership(user, company, mapping, profile, progress)
                or failure
            )
        # Commit resolved links before reporting a conflict or retrying a provider call.
        if failure is not None:
            raise failure
    except ZendeskProvisioningConflict as error:
        log.warning("Zendesk company membership conflict for user %s: %s", user_id, error.code)
        return error.code


@shared_task(
    acks_late=True,
    autoretry_for=RETRYABLE_ERRORS,
    retry_backoff=2,
    retry_kwargs={"max_retries": 3},
)
@skip_if_read_only_mode
def remove_stale_zendesk_memberships(user_id, zendesk_user_id, organization_ids):
    """Remove captured company memberships, preserving this user's current company."""
    failure = None
    try:
        user = get_user_model().all_users.filter(pk=user_id).first()
        email = user.email.strip().casefold() if user else None
        with lock_account_email(email) if email is not None else nullcontext():
            user = get_user_model().all_users.filter(pk=user_id).first()
            if user and user.email.strip().casefold() != email:
                raise ZendeskMembershipChanged("Account email changed")
            organization_ids = {canonical_zendesk_id(value) for value in organization_ids}
            if (
                user
                and Profile.all_profiles.filter(user=user, zendesk_id=zendesk_user_id).exists()
            ):
                company = get_sync_company(user)
                current_id = (
                    ZendeskOrganization.objects.filter(group_profile=company)
                    .values_list("zendesk_id", flat=True)
                    .first()
                )
                if current_id:
                    organization_ids.discard(canonical_zendesk_id(current_id))
            if not organization_ids:
                return
            remove_zendesk_company_memberships(
                ZendeskClient(disable_cache=True, ratelimit_budget=0),
                user_id=user_id,
                zendesk_user_id=zendesk_user_id,
                organization_ids=organization_ids,
            )
    except ZendeskProvisioningConflict as error:
        log.warning("Zendesk company membership conflict for user %s: %s", user_id, error.code)
    except ZENDESK_PROVIDER_ERRORS as error:
        failure = ZendeskUnavailable.from_error(error)
        log.warning("Zendesk unavailable for user %s: %s %s", user_id, *failure.args)
    # Raised outside the handler so the provider error is not chained as its context.
    if failure is not None:
        raise failure


@shared_task
@skip_if_read_only_mode
def remove_inactive_users_from_groups():
    """Remove users inactive for 6+ months from all group membership and leadership roles."""
    User = get_user_model()
    cutoff = timezone.now() - timedelta(days=settings.INACTIVE_GROUP_MEMBER_RETENTION_DAYS)

    # Identify removable users. Evaluate the query once here, in order to avoid
    # multiple evaluations if left for evaluation within each of query below.
    removable_user_ids = list(
        User.objects.filter(is_active=False)
        .filter(Q(groups__isnull=False) | Q(groupprofile__isnull=False))
        .annotate(
            deactivated=Subquery(
                Deactivation.objects.filter(user=OuterRef("pk"))
                .order_by("-date")
                .values("date")[:1]
            )
        )
        .filter(deactivated__lte=cutoff)
        .values_list("pk", flat=True)
        .distinct()
    )

    if not removable_user_ids:
        log.info("No inactive users found to remove from their groups.")
        return

    # Identify root group-profiles that would be left leaderless.
    vulnerable_roots = (
        GroupProfile.objects.filter(depth=1)
        .annotate(
            total_leaders=Count("leaders"),
            removable_leaders=Count("leaders", filter=Q(leaders__in=removable_user_ids)),
        )
        .filter(total_leaders__gt=0, total_leaders=F("removable_leaders"))
    )

    for prof in vulnerable_roots.select_related("group"):
        log.warning(
            "Skipping the removal of inactive leader(s) from the root "
            f'group "{prof}" because it would become leaderless.'
        )

    enterprise_user_ids = list(
        User.groups.through.objects.filter(
            user_id__in=removable_user_ids,
            group_id__in=enterprise_profiles().values("group_id"),
        )
        .values_list("user_id", flat=True)
        .distinct()
    )
    organization_ids = tuple(
        company_organization_ids(
            User.groups.through.objects.filter(user_id__in=enterprise_user_ids).values("group_id")
        )
    )

    # Bulk delete using the implicit "through" models for efficiency.
    # Bulk delete leaders, excluding those who were protected from removal.
    leaders_removed, _ = (
        GroupProfile.leaders.through.objects.filter(user__in=removable_user_ids)
        .exclude(groupprofile__in=vulnerable_roots)
        .delete()
    )
    # Bulk delete members, excluding those who were protected from removal as leaders.
    members_removed, _ = (
        User.groups.through.objects.filter(user__in=removable_user_ids)
        # Exclude members that are also leaders that could not be removed.
        .exclude(
            Exists(
                GroupProfile.leaders.through.objects.filter(
                    user_id=OuterRef("user_id"),
                    groupprofile__group_id=OuterRef("group_id"),
                    groupprofile__in=vulnerable_roots,
                )
            )
        )
        .delete()
    )
    queue_enterprise_zendesk_sync(enterprise_user_ids, removed_organization_ids=organization_ids)

    log.info(
        f"Removed {leaders_removed} inactive leader(s) and "
        f"{members_removed} inactive member(s) from their groups."
    )
