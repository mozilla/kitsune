from hashlib import sha1
import json
import logging
import time

from django.conf import settings

from cronjobs import register
from statsd import statsd

from kitsune.offline.utils import (
    bundle_for_product,
    redis_bundle_name,
    merge_bundles
)
from kitsune.products.models import Product
from kitsune.sumo.utils import uselocale
from kitsune.sumo.redis_utils import redis_client


log = logging.getLogger('k.offline')


@register
def build_kb_bundles(products=('firefox-os', 'firefox', 'mobile')):
    redis = redis_client('default')

    start_time = time.time()
    size = 0

    products = [Product.objects.get(slug=p) for p in products]
    with statsd.timer('offline.build_kb_bundles.time_elapsed'):
        for locale in settings.SUMO_LANGUAGES:
            for product in products:
                with uselocale(locale):
                    bundle = merge_bundles(bundle_for_product(product, locale))

                bundle = json.dumps(bundle)
                bundle_hash = sha1(bundle).hexdigest()  # track version
                name = redis_bundle_name(locale.lower(), product.slug.lower())

                redis.hset(name, 'hash', bundle_hash)
                redis.hset(name, 'bundle', bundle)

                size += len(bundle)

    time_taken = time.time() - start_time
    log.info('Generated all offline bundles. '
             'Size: {0}. Took {1} seconds'.format(size, time_taken))
