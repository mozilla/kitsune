import jingo

from landings.utils import show_ia
from landings.views import old_products
from products.models import Product


def product_list(request):
    """The product picker page."""
    if not show_ia(request):
        return old_products(request)

    products = Product.objects.filter(visible=True)
    return jingo.render(request, 'products/products.html', {
        'products': products})
