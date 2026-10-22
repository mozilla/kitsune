from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from kitsune.products.managers import CURATED_BLOCKS_CACHE_KEY
from kitsune.products.models import CuratedBlock, CuratedBlockItem, Topic, TopicSlugHistory


@receiver(pre_save, sender=Topic)
def update_topic_slug_history(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.slug != instance.slug:
            try:
                old_topic = TopicSlugHistory.objects.get(topic=instance)
                old_topic.slug = old_instance.slug
                old_topic.topic = instance
                old_topic.save()
            except TopicSlugHistory.DoesNotExist:
                TopicSlugHistory.objects.create(topic=instance, slug=old_instance.slug)


@receiver([post_save, post_delete], sender=CuratedBlock)
@receiver([post_save, post_delete], sender=CuratedBlockItem)
def clear_curated_blocks_cache(sender, instance, **kwargs):
    if sender is CuratedBlock:
        owner = (instance.topic_id, instance.product_id)
    else:
        owner = (
            CuratedBlock.objects.filter(pk=instance.block_id)
            .values_list("topic_id", "product_id")
            .first()
        )
        if owner is None:
            return

    topic_id, product_id = owner
    keys = [
        CURATED_BLOCKS_CACHE_KEY.format(topic_id=topic_id, product_id=product_id, locale=locale)
        for locale in settings.SUMO_LANGUAGES
    ]
    # Clear after commit so a concurrent request can't re-cache the old rows meanwhile.
    transaction.on_commit(lambda: cache.delete_many(keys))
