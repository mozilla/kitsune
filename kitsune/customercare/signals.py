from django.contrib.auth.models import User
from django.db import transaction
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from kitsune.customercare.tasks import (
    chat_product_slugs,
    had_chat,
    revoke_chat_tickets,
    revoke_company_chat_tickets,
    update_zendesk_user,
)
from kitsune.groups.models import GroupProfile
from kitsune.products.models import Product, SupportContract, SupportCoverage
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
    # TODO: avoid duplicate Zendesk syncs when both User and Profile are saved.

    user = instance
    if sender == Profile:
        user = instance.user
        if update_fields and len(update_fields) == 1 and "zendesk_id" in update_fields:
            return

    try:
        if user.profile.zendesk_id:
            transaction.on_commit(
                lambda user_id=user.pk: update_zendesk_user.delay(user_id),
                using=kwargs.get("using"),
                robust=True,
            )
    except Profile.DoesNotExist:
        pass


@receiver(pre_delete, sender=User, dispatch_uid="customercare.signals.on_user_deletion.User")
def on_user_deletion(sender, instance, **kwargs):
    # Django sends this inside the delete's transaction, before the profile is gone.
    if had_chat(GroupProfile.objects.containing(instance)):
        revoke_chat_tickets(instance, using=kwargs.get("using"))


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
    if getattr(instance, "_is_being_deactivated", False) and had_chat(
        GroupProfile.objects.containing(instance)
    ):
        revoke_chat_tickets(instance, using=kwargs.get("using"))


@receiver(
    pre_save,
    sender=SupportContract,
    dispatch_uid="customercare.signals.check_chat_change.SupportContract",
)
@receiver(
    pre_save,
    sender=SupportCoverage,
    dispatch_uid="customercare.signals.check_chat_change.SupportCoverage",
)
def check_chat_change(sender, instance, **kwargs):
    # Checked before the save, while the database still has the old contract or coverage.
    instance._chat_before = None
    if instance.pk is None:
        return
    contract_lookup = (
        "support_contracts" if sender is SupportContract else "support_contracts__coverages"
    )
    company = GroupProfile.objects.filter(**{contract_lookup: instance.pk}).first()
    if company is not None:
        instance._chat_before = (company, chat_product_slugs(company, include_expired=True))


@receiver(
    post_save,
    sender=SupportContract,
    dispatch_uid="customercare.signals.on_chat_change.SupportContract",
)
@receiver(
    post_save,
    sender=SupportCoverage,
    dispatch_uid="customercare.signals.on_chat_change.SupportCoverage",
)
def on_chat_change(sender, instance, **kwargs):
    # Compared per company, so a product another contract still covers with chat keeps it.
    if before := getattr(instance, "_chat_before", None):
        company, products = before
        if lost_products := products - chat_product_slugs(company):
            revoke_company_chat_tickets(company, lost_products, using=kwargs.get("using"))


@receiver(pre_save, sender=Product, dispatch_uid="customercare.signals.check_archival.Product")
def check_archival(sender, instance, update_fields=None, **kwargs):
    instance._is_being_archived = (
        instance.is_archived
        and instance.pk is not None
        and (update_fields is None or "is_archived" in update_fields)
        and Product.objects.filter(pk=instance.pk, is_archived=False).exists()
    )


@receiver(post_save, sender=Product, dispatch_uid="customercare.signals.on_archival.Product")
def on_archival(sender, instance, **kwargs):
    if getattr(instance, "_is_being_archived", False):
        chat_coverages = SupportCoverage.objects.in_effect().filter(
            product=instance, includes_chat=True
        )
        for company in GroupProfile.objects.filter(
            pk__in=chat_coverages.values("contract__company")
        ):
            revoke_company_chat_tickets(company, {instance.slug}, using=kwargs.get("using"))
