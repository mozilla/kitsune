from django.shortcuts import get_object_or_404, render

import waffle
from mobility.decorators import mobile_template

from kitsune.products.models import Product, Topic as NewTopic
from kitsune.topics.models import Topic, HOT_TOPIC_SLUG
from kitsune.wiki.facets import topics_for, documents_for


@mobile_template('products/{mobile/}products.html')
def product_list(request, template):
    """The product picker page."""
    products = Product.objects.filter(visible=True)
    return render(request, template, {
        'products': products})


@mobile_template('products/{mobile/}product.html')
def product_landing(request, template, slug):
    """The product landing page."""
    product = get_object_or_404(Product, slug=slug)

    new_topics = waffle.flag_is_active(request, 'new-topics')

    try:
        if new_topics:
            topic = NewTopic.objects.get(
                product=product, slug=HOT_TOPIC_SLUG)
        else:
            topic = Topic.objects.get(slug=HOT_TOPIC_SLUG)
        hot_docs, fallback_hot_docs = documents_for(
            locale=request.LANGUAGE_CODE,
            topics=[topic],
            products=[product],
            new_topics=new_topics)
    except Topic.DoesNotExist:
        # "hot" topic doesn't exist, move on.
        hot_docs = fallback_hot_docs = None

    return render(request, template, {
        'product': product,
        'products': Product.objects.filter(visible=True),
        'topics': topics_for(
            products=[product],
            new_topics=new_topics,
            include_subtopics=False),
        'hot_docs': hot_docs,
        'fallback_hot_docs': fallback_hot_docs,
        'search_params': {'product': slug}})


@mobile_template('products/{mobile/}documents.html')
def document_listing(request, template, product_slug, topic_slug):
    """The document listing page for a product + topic."""
    product = get_object_or_404(Product, slug=product_slug)

    new_topics = waffle.flag_is_active(request, 'new-topics')

    if new_topics:
        topic = get_object_or_404(NewTopic, slug=topic_slug, product=product)
    else:
        topic = get_object_or_404(Topic, slug=topic_slug)

    documents, fallback_documents = documents_for(
        locale=request.LANGUAGE_CODE, products=[product], topics=[topic],
        new_topics=new_topics)

    return render(request, template, {
        'product': product,
        'topic': topic,
        'topics': topics_for(products=[product], new_topics=new_topics),
        'subtopics': topics_for(
            products=[product], parent=topic, new_topics=new_topics),
        'documents': documents,
        'fallback_documents': fallback_documents,
        'search_params': {'product': product_slug}})
