from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.conf import settings
from kitsune.users.models import Profile
from kitsune.search.v2.es7_utils import (
    index_object,
    delete_object,
    remove_from_field,
)
from kitsune.products.models import Product


@receiver(post_save, sender=User)
@receiver(post_save, sender=Profile)
@receiver(m2m_changed, sender=User.groups.through)
@receiver(m2m_changed, sender=Profile.products.through)
def handle_profile_save(instance, **kwargs):
    if getattr(kwargs, "action", "").startswith("pre_"):
        # skip pre m2m_changed signals
        return
    if settings.ES_LIVE_INDEXING:
        index_object.delay("ProfileDocument", instance.pk)


@receiver(post_delete, sender=Profile)
def handle_profile_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        delete_object.delay("ProfileDocument", instance.pk)


@receiver(post_delete, sender=Group)
def handle_group_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        remove_from_field.delay("ProfileDocument", "group_ids", instance.pk)


@receiver(post_delete, sender=Product)
def handle_product_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        remove_from_field.delay("ProfileDocument", "product_ids", instance.pk)
