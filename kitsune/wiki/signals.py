from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from kitsune.wiki.models import Document


@receiver(m2m_changed, sender=Document.topics.through)
def handle_document_topics_change(sender, instance, action, **kwargs):
    """When a document's topics change, propagate to translations if needed."""
    if action in ("post_add", "post_remove", "post_clear"):
        instance.propagate_topics_to_translations()
