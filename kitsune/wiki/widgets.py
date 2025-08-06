import json
from collections.abc import Iterable

from django import forms
from django.template.loader import render_to_string

from kitsune.products.models import Product, Topic
from kitsune.wiki.models import Document


class TopicsWidget(forms.widgets.SelectMultiple):
    """A widget to render topics and their subtopics as checkboxes."""

    def set_topic_attributes(self, topic, selected_topics, topic_subtopics, product_ids):
        topic.checked = str(topic.id) in selected_topics
        topic.products_as_json = json.dumps(product_ids.get(topic.id, []))
        topic.my_subtopics = topic_subtopics.get(topic.id, [])
        for subtopic in topic.my_subtopics:
            self.set_topic_attributes(subtopic, selected_topics, topic_subtopics, product_ids)

    def render(self, name, value, attrs=None, renderer=None):
        selected_topics = set(map(str, value or []))
        topics_and_subtopics = Topic.active.prefetch_related("products").select_related("parent")

        topic_subtopics = {}
        product_ids = {}
        topics = []

        for topic in topics_and_subtopics:
            if topic.parent_id is None:
                topics.append(topic)
            else:
                topic_subtopics.setdefault(topic.parent_id, []).append(topic)

            product_ids[topic.id] = [str(id) for id in topic.products.values_list("id", flat=True)]

        for topic in topics:
            self.set_topic_attributes(topic, selected_topics, topic_subtopics, product_ids)

        return render_to_string(
            "wiki/includes/topics_widget.html",
            {
                "topics": topics,
                "name": name,
            },
        )


class ProductsWidget(forms.widgets.SelectMultiple):
    """A widget to render the products as checkboxes."""

    def render(self, name, value, attrs=None, renderer=None):
        selected_products = set(map(str, value or []))
        products = Product.active.prefetch_related("m2m_topics")

        for product in products:
            product.checked = str(product.id) in selected_products
            product.topics_as_json = json.dumps(
                list(map(str, product.m2m_topics.values_list("id", flat=True)))
            )

        return render_to_string(
            "wiki/includes/products_widget.html",
            {
                "products": products,
                "name": name,
            },
        )


class RelatedDocumentsWidget(forms.widgets.SelectMultiple):
    """A widget to render the related documents list and search field."""

    def __init__(self, attrs=None):
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if isinstance(value, int):
            document_ids = [value]
        elif not isinstance(value, str) and isinstance(value, Iterable):
            document_ids = list(value)
        else:
            document_ids = []

        if document_ids:
            # Get the documents by their IDs
            related_documents = Document.objects.filter(id__in=document_ids)
        else:
            related_documents = Document.objects.none()

        return render_to_string(
            "wiki/includes/related_docs_widget.html",
            {"related_documents": related_documents, "name": name},
        )
