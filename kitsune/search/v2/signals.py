from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from kitsune.users.models import Profile
from kitsune.search.v2.es7_utils import index_object, delete_object
from kitsune.products.models import Product


@receiver(post_save, sender=User)
@receiver(post_save, sender=Profile)
@receiver(m2m_changed, sender=User.groups.through)
@receiver(m2m_changed, sender=Profile.products.through)
def handle_profile_save(instance, **kwargs):
    index_object.delay("ProfileDocument", instance.pk)


@receiver(post_save, sender=Group)
def handle_group_save(instance, **kwargs):
    for user in User.objects.filter(groups=instance):
        index_object.delay("ProfileDocument", user.pk)


@receiver(post_save, sender=Product)
def handle_product_save(instance, **kwargs):
    for user in instance.subscribed_users.all():
        index_object.delay("ProfileDocument", user.pk)


@receiver(post_delete, sender=Profile)
def handle_profile_delete(instance, **kwargs):
    delete_object("ProfileDocument", instance.pk)
