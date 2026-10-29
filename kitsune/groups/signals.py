import logging

from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from kitsune.customercare.models import ZendeskOrganization
from kitsune.groups.membership import (
    company_organization_ids,
    enterprise_profiles,
    guard_enterprise_memberships,
    queue_chat_revocation,
    queue_enterprise_zendesk_sync,
)
from kitsune.groups.models import GroupProfile
from kitsune.groups.tasks import remove_stale_zendesk_memberships
from kitsune.users.models import Profile

log = logging.getLogger("k.groups")


@receiver(
    m2m_changed,
    sender=User.groups.through,
    dispatch_uid="groups.guard_enterprise_memberships",
)
def guard_company_memberships(sender, instance, action, reverse, pk_set, using, **kwargs):
    if action != "pre_add" or not pk_set:
        return

    user_ids = pk_set if reverse else (instance.pk,)
    group_ids = (instance.pk,) if reverse else pk_set
    # Django's M2M mutation is already atomic. These transaction-scoped locks
    # remain held after pre_add returns, through the insertion and outer commit.
    with guard_enterprise_memberships(user_ids, group_ids, using=using):
        pass


@receiver(
    m2m_changed,
    sender=User.groups.through,
    dispatch_uid="groups.sync_enterprise_zendesk_memberships",
)
def sync_company_memberships(sender, instance, action, reverse, pk_set, using, **kwargs):
    if action not in ("post_add", "post_remove", "pre_clear"):
        return
    if action != "pre_clear" and not pk_set:
        return
    enterprise_groups = enterprise_profiles(using)
    if reverse:
        if not enterprise_groups.filter(group_id=instance.pk).exists():
            return
        user_ids = (
            sender.objects.using(using)
            .filter(group_id=instance.pk)
            .values_list("user_id", flat=True)
            if action == "pre_clear"
            else pk_set
        )
        group_ids = (instance.pk,)
    else:
        group_ids = (
            sender.objects.using(using)
            .filter(user_id=instance.pk)
            .values_list("group_id", flat=True)
            if action == "pre_clear"
            else pk_set
        )
        if not enterprise_groups.filter(group_id__in=group_ids).exists():
            return
        user_ids = (instance.pk,)
    organization_ids = ()
    if action != "post_add":
        organization_ids = company_organization_ids(group_ids, using=using)
        queue_chat_revocation(user_ids, group_ids, using=using)
    queue_enterprise_zendesk_sync(user_ids, using=using, removed_organization_ids=organization_ids)


@receiver(
    pre_delete,
    sender=User,
    dispatch_uid="groups.remove_stale_zendesk_memberships",
)
def remove_deleted_user_memberships(sender, instance, using, **kwargs):
    """Capture remote cleanup before the user's profile and memberships cascade."""
    profiles = Profile.all_profiles.using(using)
    profile = profiles.filter(user_id=instance.pk).first()
    if profile is None or not profile.zendesk_id:
        return
    if profiles.filter(zendesk_id=profile.zendesk_id).exclude(pk=profile.pk).exists():
        log.warning(
            "Zendesk deleted-user membership conflict for user %s: %s",
            instance.pk,
            "account_conflict",
        )
        return

    organization_ids = tuple(
        ZendeskOrganization.objects.using(using).linked_ids().order_by("zendesk_id")
    )
    if not organization_ids:
        return
    transaction.on_commit(
        lambda user_id=instance.pk, zendesk_user_id=profile.zendesk_id: (
            remove_stale_zendesk_memberships.delay(user_id, zendesk_user_id, organization_ids)
        ),
        using=using,
        robust=True,
    )


@receiver(
    m2m_changed,
    sender=GroupProfile.visible_to_groups.through,
    dispatch_uid="groups.propagate_visible_to_groups",
)
def propagate_visible_to_groups(sender, instance, action, **kwargs):
    """
    Propagate visible_to_groups changes from parent to all descendants.

    When a parent's visible_to_groups is modified, all descendants
    automatically inherit the same setting, mirroring visibility inheritance.
    """
    if action not in ["post_add", "post_remove", "post_clear"]:
        return

    descendants = GroupProfile.objects.get_descendants(instance)

    if not descendants.exists():
        return

    parent_groups = instance.visible_to_groups.all()

    for descendant in descendants:
        descendant.visible_to_groups.set(parent_groups)


@receiver(
    post_save,
    sender=GroupProfile,
    dispatch_uid="groups.sync_visible_to_groups_on_create",
)
def sync_visible_to_groups_on_create(sender, instance, **kwargs):
    """
    Sync visible_to_groups from parent when child is created or moved.

    This handles initial inheritance since M2M relationships can only
    be set after the instance has been saved with a primary key.
    """
    if not getattr(instance, "_needs_visible_to_groups_sync", False):
        return

    if len(instance.path) > instance.steplen:
        parent = GroupProfile.objects.get_parent(instance)
        if parent:
            instance.visible_to_groups.set(parent.visible_to_groups.all())

    instance._needs_visible_to_groups_sync = False


@receiver(pre_delete, sender=Group, dispatch_uid="groups.delete_group_profiles")
def delete_group_profiles(sender, instance, using, **kwargs):
    """
    Delete a group's profiles through treebeard rather than via cascade
    in order to properly maintain the profile tree. This also deletes the
    subgroups' Groups (see GroupProfileQuerySet.delete).
    """
    GroupProfile.objects.using(using).filter(group_id=instance.pk).delete(
        _sync_enterprise_memberships=not getattr(
            instance, "_enterprise_memberships_captured", False
        )
    )
