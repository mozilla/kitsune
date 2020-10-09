from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.conf import settings
from kitsune.users.models import Profile
from kitsune.search.v2.es7_utils import index_object, delete_object
from kitsune.products.models import Product
from kitsune.forums.models import Thread, Post


@receiver(post_save, sender=User)
@receiver(post_save, sender=Profile)
@receiver(m2m_changed, sender=User.groups.through)
@receiver(m2m_changed, sender=Profile.products.through)
def handle_profile_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        index_object.delay("ProfileDocument", instance.pk)


@receiver(post_save, sender=Group)
def handle_group_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        for user in User.objects.filter(groups=instance):
            index_object.delay("ProfileDocument", user.pk)


@receiver(post_save, sender=Product)
def handle_product_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        for user in instance.subscribed_users.all():
            index_object.delay("ProfileDocument", user.pk)


@receiver(post_delete, sender=Profile)
def handle_profile_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        delete_object.delay("ProfileDocument", instance.pk)


@receiver(post_save, sender=Thread)
def handle_forum_thread_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        for post in instance.post_set.all():
            index_object.delay("ForumDocument", post.id)


@receiver(post_delete, sender=Thread)
def handle_forum_thread_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        for post in instance.post_set.all():
            delete_object.delay("ForumDocument", post.id)


@receiver(post_save, sender=Post)
def handle_forum_post_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        index_object.delay("ForumDocument", instance.id)


@receiver(post_delete, sender=Post)
def handle_forum_post_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        delete_object.delay("ForumDocument", instance.id)
