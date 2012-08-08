from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

import jingo

from landings.utils import show_ia
from landings.views import old_products
from products.models import Product
from sumo.urlresolvers import reverse
from wiki.facets import topics_for


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
    return jingo.render(request, 'products/product.html', {
        'product': product,
        'topics': topics_for(products=[product])})
