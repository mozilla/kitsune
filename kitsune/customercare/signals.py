from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from kitsune.sumo.utils import dedupe_task
from kitsune.users.models import Profile


@receiver(
    post_save,
    sender=User,
    dispatch_uid="customercare.signals.on_save_update_zendesk_user.User",
)
@receiver(
    post_save,
    sender=Profile,
    dispatch_uid="customercare.signals.on_save_update_zendesk_user.Profile",
)
def on_save_update_zendesk_user(sender, instance, update_fields=None, **kwargs):
    user = instance
    if sender == Profile:
        user = instance.user
        if update_fields and len(update_fields) == 1 and "zendesk_id" in update_fields:
            # do nothing if the only thing updated is the zendesk_id
            return

    try:
        if user.profile.zendesk_id:
            dedupe_task("kitsune.customercare.tasks.update_zendesk_user", (user.pk,))
    except Profile.DoesNotExist:
        pass
