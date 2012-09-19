from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

import jingo

from landings.views import old_products
from products.models import Product
from sumo.urlresolvers import reverse
from topics.models import Topic, HOT_TOPIC_SLUG
from wiki.facets import topics_for, documents_for


def product_list(request):
    """The product picker page."""
    products = Product.objects.filter(visible=True)
    return jingo.render(request, 'products/products.html', {
        'products': products})


def product_landing(request, slug):
    """The product landing page."""
    product = get_object_or_404(Product, slug=slug)

    try:
        hot_docs, fallback_hot_docs = documents_for(
            locale=request.locale,
            topics=[Topic.objects.get(slug=HOT_TOPIC_SLUG)],
            products=[product])
    except Topic.DoesNotExist:
        # "hot" topic doesn't exist, move on.
        hot_docs = fallback_hot_docs = None
    

    return jingo.render(request, 'products/product.html', {
        'product': product,
        'products': Product.objects.filter(visible=True),
        'topics': topics_for(products=[product]),
        'hot_docs': hot_docs,
        'fallback_hot_docs': fallback_hot_docs})


def document_listing(request, product_slug, topic_slug):
    """The document listing page for a product + topic."""
    product = get_object_or_404(Product, slug=product_slug)
    topic = get_object_or_404(Topic, slug=topic_slug)
    refine_slug = request.GET.get('refine')
    if refine_slug:
        refine = get_object_or_404(Topic, slug=refine_slug)
        topics = [topic, refine]
    else:
        refine = None
        topics = [topic]
    documents, fallback_documents = documents_for(
        locale=request.locale, products=[product], topics=topics)

    return jingo.render(request, 'products/documents.html', {
        'product': product,
        'topic': topic,
        'topics': topics_for(products=[product]),
        'refine': refine,
        'refine_topics': topics_for(products=[product], topics=[topic]),
        'documents': documents,
        'fallback_documents': fallback_documents})
