from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from kitsune.products.models import (
    ProductSupportConfig,
    SupportOrganization,
    Topic,
    TopicSlugHistory,
)


@receiver(m2m_changed, sender=User.groups.through)
def clear_enterprise_banner_cache(sender, instance, action, pk_set, **kwargs):
    if action not in ("post_add", "post_remove", "post_clear"):
        return
    if isinstance(instance, User):
        cache.delete(f"enterprise_hybrid_banner:{instance.pk}")
    elif pk_set is not None:
        cache.delete_many([f"enterprise_hybrid_banner:{pk}" for pk in pk_set])


@receiver(post_save, sender=ProductSupportConfig)
@receiver(pre_delete, sender=ProductSupportConfig)
def clear_enterprise_banner_cache_on_config_change(sender, instance, **kwargs):
    group_pks = instance.support_organizations.values_list("group_id", flat=True)
    if not group_pks:
        return
    user_pks = User.objects.filter(groups__in=group_pks).values_list("pk", flat=True).distinct()
    cache.delete_many([f"enterprise_hybrid_banner:{pk}" for pk in user_pks])


@receiver(pre_save, sender=SupportOrganization)
def remember_support_organization_group(sender, instance, **kwargs):
    instance._previous_group_id = (
        sender.objects.filter(pk=instance.pk).values_list("group_id", flat=True).first()
        if instance.pk
        else None
    )


@receiver(post_save, sender=SupportOrganization)
@receiver(post_delete, sender=SupportOrganization)
def clear_enterprise_banner_cache_on_organization_change(sender, instance, **kwargs):
    group_pks = {instance.group_id}
    if previous_group_id := getattr(instance, "_previous_group_id", None):
        group_pks.add(previous_group_id)
    user_pks = User.objects.filter(groups__in=group_pks).values_list("pk", flat=True).distinct()
    cache.delete_many([f"enterprise_hybrid_banner:{pk}" for pk in user_pks])


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
