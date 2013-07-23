# -*- coding: utf-8 -*-
from django.conf import settings

from kitsune.products.models import Product, Topic
from kitsune.topics.models import Topic as OldTopic
from kitsune.questions import question_config
from kitsune.questions.models import Question


def run():
    # Make sure all topics listed in kitsune.questions.question_config exist.
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

    # Assign all the right new topics to the right old topics.
    for product in Product.objects.all():
        topics = Topic.objects.filter(product=product)
        for topic in topics:
            questions = Question.objects.filter(products=product,
                                                old_topics__slug=topic.slug)
            print '%s / %s (%d questions)' % (product.title, topic.title, len(questions))
            for q in questions:
                q.topics.add(topic)