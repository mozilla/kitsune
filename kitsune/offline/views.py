import json

from django.conf import settings
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)

from kitsune.offline.utils import (cors_enabled,
                                   bundle_for_product,
                                   merge_bundles)
from kitsune.products.models import Product
from kitsune.sumo.utils import uselocale

INVALID_PRODUCT = '{"error": "not found", "reason": "invalid product"}'
INVALID_LOCALE = '{"error": "not found", "reason": "invalid locale"}'


# TODO: do not use cors for everywhere. Though we need a finalized URL.
@cors_enabled('*')
def get_bundles(request):
    if 'locales' not in request.GET or 'products' not in request.GET:
        return HttpResponseBadRequest()

    locales = request.GET.getlist('locales', [])
    products = request.GET.getlist('products', [])

    try:
        products = [Product.objects.get(slug=product) for product in products]
    except Product.DoesNotExist:
        return HttpResponseNotFound(INVALID_PRODUCT,
                                    mimetype='application/json')

    bundles = []
    for locale in locales:
        if locale.lower() not in settings.LANGUAGES:
            return HttpResponseNotFound(INVALID_LOCALE,
                                        mimetype='application/json')

        for product in products:
            # We need to switch locale as topic names are translated via _
            with uselocale(locale):
                bundles.append(bundle_for_product(product, locale))

    # and yes, even if there is only one bundle we need to merge. The bundle
    # from bundle_for_product is in a dictionary based format. We need it in a
    # list based format.
    data = json.dumps(merge_bundles(*bundles))
    length = len(data)

    response = HttpResponse(data, mimetype='application/json')
    response['Content-Length'] = length
    return response
