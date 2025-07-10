from django.db.models.signals import post_delete, post_save

from kitsune.forums.models import Post, Thread
from kitsune.search.decorators import search_receiver
from kitsune.search.es_utils import delete_object, index_object, index_objects_bulk


@search_receiver(post_save, Thread)
def handle_forum_thread_save(instance, **kwargs):
    index_objects_bulk.delay("ForumDocument", list(instance.post_set.values_list("pk", flat=True)))


@search_receiver(post_save, Post)
def handle_forum_post_save(instance, **kwargs):
    index_object.delay("ForumDocument", instance.id)


@search_receiver(post_delete, Post)
def handle_forum_post_delete(instance, **kwargs):
    delete_object.delay("ForumDocument", instance.id)
