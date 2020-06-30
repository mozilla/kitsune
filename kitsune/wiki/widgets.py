import collections

from django import forms
from django.template.loader import render_to_string

from kitsune.products.models import Topic
from kitsune.wiki.models import Document


class ProductTopicsAndSubtopicsWidget(forms.widgets.SelectMultiple):
    """A widget to render topics organized by product and with subtopics."""

    def render(self, name, value, attrs=None, renderer=None):
        topics_and_subtopics = Topic.objects.all()
        topics = [t for t in topics_and_subtopics if t.parent_id is None]

        for topic in topics:
            self.process_topic(value, topic)

            topic.my_subtopics = [t for t in topics_and_subtopics if t.parent_id == topic.id]

            for subtopic in topic.my_subtopics:
                self.process_topic(value, subtopic)

        return render_to_string(
            "wiki/includes/product_topics_widget.html", {"topics": topics, "name": name,}
        )

    def process_topic(self, value, topic):
        if isinstance(value, int) and topic.id == value:
            topic.checked = True
        elif (
            not isinstance(value, str)
            and isinstance(value, collections.Iterable)
            and topic.id in value
        ):
            topic.checked = True
        else:
            topic.checked = False


class RelatedDocumentsWidget(forms.widgets.SelectMultiple):
    """A widget to render the related documents list and search field."""

    def render(self, name, value, attrs=None, renderer=None):
        if isinstance(value, int):
            related_documents = Document.objects.filter(id__in=[value])
        elif not isinstance(value, str) and isinstance(value, collections.Iterable):
            related_documents = Document.objects.filter(id__in=value)
        else:
            related_documents = Document.objects.none()

        return render_to_string(
            "wiki/includes/related_docs_widget.html",
            {"related_documents": related_documents, "name": name},
        )
