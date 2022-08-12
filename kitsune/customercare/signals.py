from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from zenpy.lib.exception import ZenpyException

from kitsune.customercare.tasks import update_zendesk_user
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
    except (Profile.DoesNotExist, ZenpyException):
        pass
