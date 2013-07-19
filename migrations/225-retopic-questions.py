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
            topic = Topic.uncached.get(slug=old_topic.slug, product=product)

            i = 0
            # Add the new topic to the appropriate docs.
            for q in questions:
                i += 1
                #print i, '\r',
                q.topics.add(topic)
