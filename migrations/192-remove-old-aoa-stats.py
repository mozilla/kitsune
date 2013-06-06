from django.conf import settings

from kitsune.customercare.cron import get_customercare_stats
from kitsune.sumo.redis_utils import redis_client, RedisError

try:
    print "Removing old data"
    redis = redis_client(name='default')
    redis.delete(settings.CC_TOP_CONTRIB_CACHE_KEY)

    print "Collecting new data."
    get_customercare_stats()

    print "Done"
except RedisError:
    print "This migration needs Redis to be done."
