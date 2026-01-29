from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from kitsune.groups.models import GroupProfile


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

    descendants = instance.get_descendants()

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
        parent = instance.get_parent()
        if parent:
            instance.visible_to_groups.set(parent.visible_to_groups.all())

    instance._needs_visible_to_groups_sync = False
