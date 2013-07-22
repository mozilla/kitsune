# -*- coding: utf-8 -*-
from random import random

from django.conf import settings

from kitsune.products.models import Product, Topic
from kitsune.topics.models import Topic as OldTopic
from kitsune.questions import question_config
from kitsune.questions.models import Question


def run():
    for prod_desc in question_config.products.values():
        for product_slug in prod_desc.get('products', []):
            product = Product.objects.get(slug=product_slug)
            for topic_desc in prod_desc['categories'].values():
                _, created = Topic.objects.get_or_create(
                    slug=topic_desc['topic'],
                    product=product,
                    defaults={
                        'title': topic_desc['name'],
                        'display_order': 1000,
                    }
                )
                if created:
                    print ('Created missing topic %s/%s'
                           % (product_slug, topic_desc['topic']))
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
                topic = Topic.uncached.get(slug=old_topic.slug, product=product)

                # Add the new topic to the appropriate docs.
                for q in questions:
                    q.topics.add(topic)
            except Topic.DoesNotExist:
                # This is rare, leave these questions without a topic.
                print ('WARNING - No topic matching %s / %s, '
                       'leaving %d questions possibly without a topic.'
                       % (product.title, old_topic.title, len(questions)))
