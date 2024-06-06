from django.db.models.signals import pre_save
from django.dispatch import receiver

from kitsune.products.models import Topic


@receiver(pre_save, sender=Topic)
def update_topic_slug_history(sender, instance, **kwargs):
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.slug != instance.slug:
            TopicSlugHistory.objects.create(topic=instance, slug=old_instance.slug)
