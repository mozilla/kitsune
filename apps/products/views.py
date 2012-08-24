from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

import jingo

from landings.utils import show_ia
from landings.views import old_products
from products.models import Product
from sumo.urlresolvers import reverse
from topics.models import Topic, HOT_TOPIC_SLUG
from wiki.facets import topics_for, documents_for


def product_list(request):
    """The product picker page."""
    if not show_ia(request):
        return old_products(request)

    products = Product.objects.filter(visible=True)
    return jingo.render(request, 'products/products.html', {
        'products': products})


def product_landing(request, slug):
    """The product landing page."""
    if not show_ia(request):
        return HttpResponseRedirect(reverse('products'))

    product = get_object_or_404(Product, slug=slug)
    hot_docs = documents_for(
        locale=request.locale,
        topics=[Topic.objects.get(slug=HOT_TOPIC_SLUG)],
        products=[product])
    return jingo.render(request, 'products/product.html', {
        'product': product,
        'products': Product.objects.filter(visible=True),
        'topics': topics_for(products=[product]),
        'hot_docs': hot_docs})


def document_listing(request, product_slug, topic_slug):
    """The document listing page for a product + topic."""
    if not show_ia(request):
        return HttpResponseRedirect(reverse('products'))

    product = get_object_or_404(Product, slug=product_slug)
    topic = get_object_or_404(Topic, slug=topic_slug)
    documents = documents_for(
        locale=request.locale, products=[product], topics=[topic])
    return jingo.render(request, 'products/documents.html', {
        'product': product,
        'topic': topic,
        'topics': topics_for(products=[product]),
        'documents': documents})
