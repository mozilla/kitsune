# -*- coding: utf-8 -*-
from django.conf import settings

from kitsune.products.models import Product, Topic
from kitsune.topics.models import Topic as OldTopic
from kitsune.wiki.models import Document


def run():
    # Get all the old topics.
    old_topics = OldTopic.objects.all().order_by('parent')

    # For each of the old topics...
    for old_topic in old_topics:
        # Get the documents they apply to.
        docs = Document.objects.filter(
            locale=settings.WIKI_DEFAULT_LANGUAGE,
            topics=old_topic)

        # Get the products that apply to those documents.
        products = Product.objects.filter(document__in=docs).distinct()

        # For each product, create the topic if it doesn't exist and assign it
        # to the documents.
        for product in products:
            print '=========================================================='
            print '[%s] %s' % (product, old_topic.title)
            print '=========================================================='
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

            # Add the new topic to the appropriate docs.
            for doc in docs.filter(products=product):
                print doc.title.encode('utf8')
                doc.new_topics.add(topic)

    # Make sure we have hot topics for all products.
    for product in Product.objects.all():
        try:
            Topic.uncached.get(slug='hot', product=product)
        except Topic.DoesNotExist:
            # Create the topic.
            topic = Topic.objects.create(
                title='Hot topics',
                slug='hot',
                description='Hot topics',
                product=product,
                parent=None,
                display_order=1000,
                visible=True)
