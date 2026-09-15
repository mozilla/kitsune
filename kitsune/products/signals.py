from django.core.cache import cache
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from kitsune.products.models import (
    Product,
    ProductSupportConfig,
    Topic,
    TopicSlugHistory,
    ZendeskConfig,
)
from kitsune.products.utils import ENTERPRISE_ZENDESK_CACHE_KEY


@receiver(post_save, sender=ProductSupportConfig)
@receiver(post_delete, sender=ProductSupportConfig)
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=ZendeskConfig)
def clear_enterprise_banner_cache(sender, **kwargs):
    cache.delete(ENTERPRISE_ZENDESK_CACHE_KEY)


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
