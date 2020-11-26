from django.db.models.signals import post_save, m2m_changed, post_delete
from django.dispatch import receiver
from django.conf import settings
from kitsune.search.v2.es7_utils import (
    index_object,
    delete_object,
    remove_from_field,
)
from kitsune.wiki.models import Document
from kitsune.products.models import Product, Topic


@receiver(post_save, sender=Document)
@receiver(m2m_changed, sender=Document.products.through)
@receiver(m2m_changed, sender=Document.topics.through)
def handle_document_save(instance, **kwargs):
    if getattr(kwargs, "action", "").startswith("pre_"):
        # skip pre m2m_changed signals
        return
    if settings.ES_LIVE_INDEXING:
        index_object.delay("WikiDocument", instance.pk)


@receiver(post_delete, sender=Document)
def handle_document_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        delete_object.delay("WikiDocument", instance.pk)


@receiver(post_delete, sender=Product)
def handle_product_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        remove_from_field.delay("WikiDocument", "product_ids", instance.pk)


@receiver(post_delete, sender=Topic)
def handle_topic_delete(instance, **kwargs):
    if settings.ES_LIVE_INDEXING:
        remove_from_field.delay("WikiDocument", "topic_ids", instance.pk)
