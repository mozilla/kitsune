import logging
import time

from django.conf import settings

from cronjobs import register
from statsd import statsd

from kitsune.offline.utils import (
    bundle_for_product,
    merge_bundles,
    insert_bundle_into_redis
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

                size += len(insert_bundle_into_redis(redis,
                                                     product.slug,
                                                     locale,
                                                     bundle)[0])

    time_taken = time.time() - start_time
    log.info('Generated all offline bundles. '
             'Size: {0}. Took {1} seconds'.format(size, time_taken))
