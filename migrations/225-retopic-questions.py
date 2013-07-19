# -*- coding: utf-8 -*-
from django.conf import settings

from kitsune.products.models import Product, Topic
from kitsune.topics.models import Topic as OldTopic
from kitsune.questions.models import Question


def run():
    # Get all the old topics.
    old_topics = OldTopic.objects.all().order_by('parent')

    # For each of the old topics...
    for old_topic in old_topics:
        # Get the questions they apply to.
        questions = Question.objects.filter(old_topics=old_topic)

        # Get the products that apply to those documents.
        products = Product.objects.filter(question__in=questions).distinct()

        # For each product, create the topic if it doesn't exist and
        # assign it to the documents.
        for product in products:
            print '%s / %s (%s questions)' % (product, old_topic.title, len(questions))
            try:
                topic = Topic.uncached.get(
                    slug=old_topic.slug, product=product)
            except Topic.DoesNotExist:
                # Get the new parent if it should have one.
                parent = None
                if old_topic.parent:
                    try:
                        parent = Topic.uncached.get(
                            slug=old_topic.parent.slug, product=product)
                    except Topic.DoesNotExist:
                        # Create the parent.
                        parent = Topic.objects.create(
                            title=old_topic.parent.title,
                            slug=old_topic.parent.slug,
                            description=old_topic.parent.description,
                            product=product,
                            display_order=old_topic.parent.display_order,
                            visible=old_topic.parent.visible)

                # Create the topic.
                topic = Topic.objects.create(
                    title=old_topic.title,
                    slug=old_topic.slug,
                    description=old_topic.description,
                    product=product,
                    parent=parent,
                    display_order=old_topic.display_order,
                    visible=old_topic.visible)

            i = 0
            # Add the new topic to the appropriate docs.
            for q in questions:
                i += 1
                #print i, '\r',
                q.topics.add(topic)
