from django.db.models.signals import m2m_changed, post_delete, post_save

from kitsune.products.models import Product, Topic
from kitsune.search.decorators import search_receiver
from kitsune.search.es7_utils import delete_object, index_object, remove_from_field
from kitsune.wiki.models import Document


@search_receiver(post_save, Document)
@search_receiver(m2m_changed, Document.products.through)
@search_receiver(m2m_changed, Document.topics.through)
def handle_document_save(instance, **kwargs):
    if instance.current_revision:
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
