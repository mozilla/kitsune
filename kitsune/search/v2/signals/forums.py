from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from kitsune.search.v2.es7_utils import index_object, delete_object, index_objects_bulk
from kitsune.forums.models import Thread, Post


@receiver(post_save, sender=Thread)
def handle_forum_thread_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        index_objects_bulk.delay(
            "ForumDocument", list(instance.post_set.values_list("pk", flat=True))
        )


@receiver(post_save, sender=Post)
def handle_forum_post_save(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        index_object.delay("ForumDocument", instance.id)


@receiver(post_delete, sender=Post)
def handle_forum_post_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        delete_object.delay("ForumDocument", instance.id)
