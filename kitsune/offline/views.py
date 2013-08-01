import json

from django.conf import settings
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)

from kitsune.offline.utils import (
    bundle_for_product,
    cors_enabled,
    merge_bundles,
    redis_bundle_name,
    toss_bundle_into_redis
)
from kitsune.products.models import Product
from kitsune.sumo.redis_utils import redis_client, RedisError


INVALID_PRODUCT = '{"error": "not found", "reason": "invalid product"}'
INVALID_LOCALE = '{"error": "not found", "reason": "invalid locale"}'


@cors_enabled('*')
def get_bundle(request):
    if 'locale' not in request.GET or 'product' not in request.GET:
        return HttpResponseBadRequest()

    locale = request.GET['locale']
    product = request.GET['product']
    if locale.lower() not in settings.LANGUAGES:
        return HttpResponseNotFound(INVALID_LOCALE,
                                    mimetype='application/json')

    name = redis_bundle_name(locale, product)
    try:
        redis = redis_client('default')
    except RedisError as e:
        bundle = None
        redis = None
    else:
        bundle = redis.hget(name, 'bundle')
        bundle_hash = redis.hget(name, 'hash')

    # redis.hget could return none if it does not exist.
    # if redis is not available, toss_bundle won't actually toss it.
    if bundle is None:
        try:
            product = Product.objects.get(slug=product)
        except Product.DoesNotExist:
            return HttpResponseNotFound(INVALID_PRODUCT,
                                        mimetype='application/json')
        else:
            bundle = merge_bundles(bundle_for_product(product, locale))
            bundle, bundle_hash = toss_bundle_into_redis(redis,
                                                         product.slug,
                                                         locale,
                                                         bundle)

    response = HttpResponse(bundle, mimetype='application/json')
    response['Content-Length'] = len(bundle)
    response['X-Content-Hash'] = bundle_hash
    response['Access-Control-Expose-Headers'] = \
        'Content-Length, X-Content-Hash'

    return response


@cors_enabled('*')
def bundle_meta(request):
    if 'locale' not in request.GET or 'product' not in request.GET:
        return HttpResponseBadRequest()

    locale = request.GET['locale']
    product = request.GET['product']

    name = redis_bundle_name(locale, product)
    try:
        redis = redis_client('default')
    except RedisError:
        return HttpResponse('no builds', mimetype='text/plain', status=503)

    bundle_hash = redis.hget(name, 'hash')

    if bundle_hash:
        u = {'hash': bundle_hash}
        return HttpResponse(json.dumps(u), mimetype='application/json')
    else:
        return HttpResponseNotFound('not found?', mimetype='text/plain')
