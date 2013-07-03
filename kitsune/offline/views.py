import json

from django.conf import settings
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)

from kitsune.offline.utils import (
    cors_enabled,
    merge_bundles,
    redis_bundle_name
)
from kitsune.products.models import Product
from kitsune.sumo.utils import uselocale
from kitsune.sumo.redis_utils import redis_client

INVALID_PRODUCT = '{"error": "not found", "reason": "invalid product"}'
INVALID_LOCALE = '{"error": "not found", "reason": "invalid locale"}'


@cors_enabled('*')
def get_bundle(request):
    if 'locale' not in request.GET or 'product' not in request.GET:
        return HttpResponseBadRequest()

    locale = request.GET['locale'].lower()
    product = request.GET['product'].lower()
    redis = redis_client('default')
    if locale not in settings.LANGUAGES:
        return HttpResponseNotFound(INVALID_LOCALE,
                                    mimetype='application/json')

    name = redis_bundle_name(locale, product)
    bundle = redis.hget(name, 'bundle')
    if bundle is None:
        return HttpResponseNotFound(INVALID_PRODUCT,
                                    mimetype='application/json')

    bundle_hash = redis.hget(name, 'hash')

    response = HttpResponse(bundle, mimetype='application/json')
    response['Content-Length'] = len(bundle)
    response['X-Content-Hash'] = bundle_hash
    return response

@cors_enabled('*')
def bundle_version(request):
    pass
