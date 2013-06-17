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


@cors_enabled('*')
def get_bundles(request):
    if 'locales' not in request.GET or 'products' not in request.GET:
        return HttpResponseBadRequest()

    locales = request.GET.getlist('locales', [])
    products = request.GET.getlist('products', [])

    try:
        products = [Product.objects.get(slug=product) for product in products]
    except Product.DoesNotExist:
        return HttpResponseNotFound('{"error": "not found", "reason": "invalid product"}', mimetype='application/json')

    bundles = []
    for locale in locales:
        if locale.lower() not in settings.LANGUAGES:
            return HttpResponseNotFound('{"error": "not found", "reason": "invalid locale"}', mimetype='application/json')

        for product in products:
            with uselocale(locale):
                bundles.append(bundle_for_product(product, locale))

    data = json.dumps(merge_bundles(*bundles))

    return HttpResponse(data, mimetype='application/json')

@cors_enabled('*')
def get_languages(request):
    data = json.dumps({'languages': settings.LANGUAGE_CHOICES})

    return HttpResponse(data, mimetype='application/json')
