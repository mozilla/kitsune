from django.db.models.signals import post_save, m2m_changed, post_delete
from kitsune.search.v2.es7_utils import (
    index_object,
    delete_object,
    remove_from_field,
)
from kitsune.search.v2.decorators import search_receiver
from kitsune.wiki.models import Document
from kitsune.products.models import Product, Topic


@search_receiver(post_save, Document)
@search_receiver(m2m_changed, Document.products.through)
@search_receiver(m2m_changed, Document.topics.through)
def handle_document_save(instance, **kwargs):
    index_object.delay("WikiDocument", instance.pk)


@search_receiver(post_delete, Document)
def handle_document_delete(instance, **kwargs):
    delete_object.delay("WikiDocument", instance.pk)


@search_receiver(post_delete, Product)
def handle_product_delete(instance, **kwargs):
    remove_from_field.delay("WikiDocument", "product_ids", instance.pk)


@search_receiver(post_delete, Topic)
def handle_topic_delete(instance, **kwargs):
    remove_from_field.delay("WikiDocument", "topic_ids", instance.pk)
