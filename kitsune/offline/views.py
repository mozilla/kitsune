import json

from django.conf import settings
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         HttpResponseNotFound)

from kitsune.offline.utils import redis_bundle_name
from kitsune.sumo.decorators import cors_enabled
from kitsune.sumo.redis_utils import redis_client, RedisError


INVALID_LOCALE = '{"error": "not found", "reason": "invalid locale"}'
NOT_FOUND = '{"error": "not found", "reason": "unknown"}'
BAD_REQUEST = '{"error": "bad request", "reason": "incomplete request"}'


@cors_enabled('*')
def get_bundle(request):
    if 'locale' not in request.GET or 'product' not in request.GET:
        return HttpResponseBadRequest(BAD_REQUEST, mimetype='application/json')

    locale = request.GET['locale']
    product = request.GET['product']
    if locale.lower() not in settings.LANGUAGES_DICT:
        return HttpResponseNotFound(INVALID_LOCALE,
                                    mimetype='application/json')

    name = redis_bundle_name(locale, product)
    try:
        redis = redis_client('default')
    except RedisError:
        return HttpResponse('not available yet', status=503)
    else:
        bundle = redis.hget(name, 'bundle')
        bundle_hash = redis.hget(name, 'hash')

    if bundle is None:
        return HttpResponseNotFound(NOT_FOUND, mimetype='application/json')

    response = HttpResponse(bundle, mimetype='application/json')
    response['Content-Length'] = len(bundle)
    response['X-Content-Hash'] = bundle_hash
    response['Access-Control-Expose-Headers'] = \
        'Content-Length, X-Content-Hash'

    return response


@cors_enabled('*')
def bundle_meta(request):
    """This view is responsible for update checking."""
    if 'locale' not in request.GET or 'product' not in request.GET:
        return HttpResponseBadRequest(BAD_REQUEST, mimetype='application/json')

    locale = request.GET['locale']
    product = request.GET['product']

    name = redis_bundle_name(locale, product)
    try:
        redis = redis_client('default')
    except RedisError:
        return HttpResponse('{"error": "no bundles available"}',
                            mimetype='application/json',
                            status=503)

    bundle_hash = redis.hget(name, 'hash')

    if bundle_hash:
        u = {'hash': bundle_hash}
        return HttpResponse(json.dumps(u), mimetype='application/json')
    else:
        return HttpResponseNotFound(NOT_FOUND, mimetype='application/json')


@cors_enabled('*')
def get_languages(request):
    """Responsible for telling what the support languages are"""
    languages = []
    for code, name in settings.LANGUAGE_CHOICES:
        languages.append({'id': code, 'name': name})

    return HttpResponse(json.dumps({'languages': languages}),
                        mimetype='application/json')
