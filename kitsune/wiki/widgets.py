import json
from collections.abc import Iterable

from django import forms
from django.template.loader import render_to_string

from kitsune.products.models import Product, Topic
from kitsune.wiki.models import Document


class TopicsWidget(forms.widgets.SelectMultiple):
    """A widget to render topics and their subtopics as checkboxes."""

    def render(self, name, value, attrs=None, renderer=None):
        selected_topics = set(value) if value else set()
        # Get all of the topics and their subtopics.
        topics_and_subtopics = list(Topic.active.prefetch_related("products"))
        # Get the topics only.
        topics = [t for t in topics_and_subtopics if t.parent_id is None]
        for topic in topics:
            topic.checked = topic.id in selected_topics
            topic.products_as_json = json.dumps(
                [str(id) for id in topic.products.values_list("id", flat=True)]
            )
            # Get all of the subtopics for this topic.
            topic.my_subtopics = [t for t in topics_and_subtopics if t.parent_id == topic.id]
            for subtopic in topic.my_subtopics:
                subtopic.checked = subtopic.id in selected_topics
                subtopic.products_as_json = json.dumps(
                    [str(id) for id in subtopic.products.values_list("id", flat=True)]
                )

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
        selected_products = set(value) if value else set()
        # Get all of the topics and their subtopics.
        products = list(Product.active.prefetch_related("m2m_topics"))
        for product in products:
            product.checked = product.id in selected_products
            product.topics_as_json = json.dumps(
                [str(id) for id in product.m2m_topics.values_list("id", flat=True)]
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

    def render(self, name, value, attrs=None, renderer=None):
        if isinstance(value, int):
            related_documents = Document.objects.filter(id__in=[value])
        elif not isinstance(value, str) and isinstance(value, Iterable):
            related_documents = Document.objects.filter(id__in=value)
        else:
            related_documents = Document.objects.none()

        return render_to_string(
            "wiki/includes/related_docs_widget.html",
            {"related_documents": related_documents, "name": name},
        )
