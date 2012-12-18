from django.conf import settings

from sumo.redis_utils import redis_client
from customercare.cron import get_customercare_stats


print "Removing old data"
redis = redis_client(name='default')
redis.delete(settings.CC_TOP_CONTRIB_CACHE_KEY)

print "Collecting new data."
get_customercare_stats()

print "Done"
