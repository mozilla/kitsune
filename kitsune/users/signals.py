from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

from kitsune.tidings.models import Watch


@receiver(post_save, sender=User)
def clear_watches_on_isactive_change(sender, instance, **kwargs):
    if instance.is_active is False:
        # Stop all watches for user, if any
        Watch.objects.filter(user=instance).delete()


@receiver(post_delete, sender=User)
def clear_watches_on_user_delete(sender, instance, **kwargs):
    Watch.objects.filter(user=instance).delete()
