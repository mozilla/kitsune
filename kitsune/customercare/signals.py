from django.contrib.auth.models import Group, User
from django.db.models.signals import m2m_changed, post_save, pre_delete, pre_save
from django.dispatch import receiver
from zenpy.lib.exception import ZenpyException

from kitsune.customercare.tasks import tag_chat_tickets_if_revoked, update_zendesk_user
from kitsune.groups.models import GroupProfile
from kitsune.products.models import ProductSupportConfig, SupportOrganization
from kitsune.users.models import Profile


@receiver(
    post_save, sender=User, dispatch_uid="customercare.signals.on_save_update_zendesk_user.User"
)
@receiver(
    post_save,
    sender=Profile,
    dispatch_uid="customercare.signals.on_save_update_zendesk_user.Profile",
)
def on_save_update_zendesk_user(sender, instance, update_fields=None, **kwargs):
    # TODO: dedupe signals, so calling
    # ```
    # user.profile.save()
    # user.save()
    # ```
    # doesn't update the user in zendesk twice

    user = instance
    if sender == Profile:
        user = instance.user
        if update_fields and len(update_fields) == 1 and "zendesk_id" in update_fields:
            # do nothing if the only thing updated is the zendesk_id
            return

    try:
        if user.profile.zendesk_id:
            update_zendesk_user.delay(user.pk)
    except Profile.DoesNotExist, ZenpyException:
        pass


def grants_chat(group_profiles) -> bool:
    """Whether any of these groups is a support organization's group with live chat."""
    return group_profiles.filter(group__support_organizations__include_live_chat=True).exists()


def tag_chat_tickets_of_org_members(org):
    """Queue tagging for everyone in the organization's group or its subgroups."""
    group_profile = GroupProfile.objects.filter(group_id=org.group_id).first()
    if group_profile is None:
        return
    members = (
        User.objects.filter(groups__profile__in=GroupProfile.get_tree(group_profile))
        .select_related("profile")
        .distinct()
    )
    for user in members:
        tag_chat_tickets_if_revoked(user)


@receiver(pre_delete, sender=User, dispatch_uid="customercare.signals.on_user_deletion.User")
def on_user_deletion(sender, instance, **kwargs):
    # Django sends this inside the delete's transaction, before the profile is gone.
    if grants_chat(GroupProfile.objects.containing(instance)):
        tag_chat_tickets_if_revoked(instance)


@receiver(pre_save, sender=User, dispatch_uid="customercare.signals.check_deactivation.User")
def check_deactivation(sender, instance, update_fields=None, **kwargs):
    # Checked before the save, while the database still has the old value.
    instance._is_being_deactivated = (
        not instance.is_active
        and instance.pk is not None
        and (update_fields is None or "is_active" in update_fields)
        and User.objects.filter(pk=instance.pk, is_active=True).exists()
    )


@receiver(post_save, sender=User, dispatch_uid="customercare.signals.on_deactivation.User")
def on_deactivation(sender, instance, **kwargs):
    # Queued after the save, so the task can't read the user before it's saved.
    if getattr(instance, "_is_being_deactivated", False) and grants_chat(
        GroupProfile.objects.containing(instance)
    ):
        tag_chat_tickets_if_revoked(instance)


@receiver(
    m2m_changed,
    sender=User.groups.through,
    dispatch_uid="customercare.signals.on_group_removal.User.groups",
)
def on_group_removal(sender, instance, action, reverse, pk_set, **kwargs):
    # reverse means the change came from the group's side, as in group.user_set.remove().
    if action == "post_remove":
        if reverse and grants_chat(GroupProfile.objects.containing_groups([instance.pk])):
            users = User.objects.filter(pk__in=pk_set).select_related("profile")
        elif not reverse and grants_chat(GroupProfile.objects.containing_groups(pk_set)):
            users = [instance]
        else:
            return
    elif action == "pre_clear":
        # Only now, before the clear, can we still see who or what is being cleared.
        if reverse and grants_chat(GroupProfile.objects.containing_groups([instance.pk])):
            users = instance.user_set.select_related("profile")
        elif not reverse and grants_chat(GroupProfile.objects.containing(instance)):
            users = [instance]
        else:
            return
    else:
        return

    for user in users:
        tag_chat_tickets_if_revoked(user)


@receiver(pre_delete, sender=Group, dispatch_uid="customercare.signals.on_group_deletion.Group")
def on_group_deletion(sender, instance, **kwargs):
    # A chat organization's own group takes the organization with it, and
    # on_organization_deletion covers everyone in that case.
    if instance.support_organizations.filter(include_live_chat=True).exists():
        return
    if grants_chat(GroupProfile.objects.containing_groups([instance.pk])):
        for user in instance.user_set.select_related("profile"):
            tag_chat_tickets_if_revoked(user)


@receiver(
    pre_save,
    sender=SupportOrganization,
    dispatch_uid="customercare.signals.check_organization_change.SupportOrganization",
)
def check_organization_change(sender, instance, **kwargs):
    # Checked before the save, while the database still has the old organization.
    instance._old_org_losing_chat = None
    if instance.pk is None:
        return
    old = SupportOrganization.objects.filter(pk=instance.pk, include_live_chat=True).first()
    if old is None:
        return
    # Losing chat, or moving to another group or product, both take chat away from
    # the people it covered.
    if (
        not instance.include_live_chat
        or instance.group_id != old.group_id
        or instance.config_id != old.config_id
    ):
        instance._old_org_losing_chat = old


@receiver(
    post_save,
    sender=SupportOrganization,
    dispatch_uid="customercare.signals.on_organization_change.SupportOrganization",
)
def on_organization_change(sender, instance, **kwargs):
    # Queued after the save, so the tasks can't read the organization before it's saved.
    if old := getattr(instance, "_old_org_losing_chat", None):
        tag_chat_tickets_of_org_members(old)


@receiver(
    pre_delete,
    sender=SupportOrganization,
    dispatch_uid="customercare.signals.on_organization_deletion.SupportOrganization",
)
def on_organization_deletion(sender, instance, **kwargs):
    if instance.include_live_chat:
        tag_chat_tickets_of_org_members(instance)


@receiver(
    pre_save,
    sender=ProductSupportConfig,
    dispatch_uid="customercare.signals.check_config_change.ProductSupportConfig",
)
def check_config_change(sender, instance, **kwargs):
    # Checked before the save, while the database still has the old config.
    instance._is_losing_chat = False
    if instance.pk is None:
        return
    old = ProductSupportConfig.objects.filter(
        pk=instance.pk, is_active=True, zendesk_config__isnull=False
    ).first()
    if old is None:
        return
    # Switching off, dropping Zendesk, or requiring a subscription can all take chat
    # away from the people its organizations covered.
    instance._is_losing_chat = (
        not instance.is_active
        or instance.zendesk_config_id is None
        or (instance.subscription_only and not old.subscription_only)
    )


@receiver(
    post_save,
    sender=ProductSupportConfig,
    dispatch_uid="customercare.signals.on_config_change.ProductSupportConfig",
)
def on_config_change(sender, instance, **kwargs):
    # Queued after the save, so the tasks can't read the config before it's saved.
    if getattr(instance, "_is_losing_chat", False):
        for org in instance.support_organizations.filter(include_live_chat=True):
            tag_chat_tickets_of_org_members(org)


@receiver(
    m2m_changed,
    sender=Profile.products.through,
    dispatch_uid="customercare.signals.on_subscription_removal.Profile.products",
)
def on_subscription_removal(sender, instance, action, reverse, pk_set, **kwargs):
    # Both the subscription webhook and the login sync remove products this way.
    if action != "post_remove" or reverse:
        return
    # Only products whose live chat requires a subscription matter.
    if ProductSupportConfig.objects.filter(
        product__in=pk_set,
        is_active=True,
        zendesk_config__isnull=False,
        subscription_only=True,
        support_organizations__include_live_chat=True,
    ).exists():
        tag_chat_tickets_if_revoked(instance.user)
