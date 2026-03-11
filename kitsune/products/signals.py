from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver

from kitsune.products.models import ProductSupportConfig, Topic, TopicSlugHistory


@receiver(m2m_changed, sender=User.groups.through)
@receiver(m2m_changed, sender=ProductSupportConfig.hybrid_support_groups.through)
def clear_enterprise_banner_cache(sender, instance, action, pk_set, **kwargs):
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    if isinstance(instance, User):
        cache.delete(f"enterprise_hybrid_banner:{instance.pk}")
    elif isinstance(instance, ProductSupportConfig) and pk_set is not None:
        user_pks = User.objects.filter(groups__in=pk_set).values_list("pk", flat=True)
        cache.delete_many([f"enterprise_hybrid_banner:{pk}" for pk in user_pks])
    elif pk_set is not None:
        cache.delete_many([f"enterprise_hybrid_banner:{pk}" for pk in pk_set])


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
