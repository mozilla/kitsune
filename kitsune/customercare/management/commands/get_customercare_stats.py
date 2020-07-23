import json
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from kitsune.customercare.models import Reply
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.sumo.utils import chunked

log = logging.getLogger("k.twitter")


class Command(BaseCommand):
    help = "Generate customer care stats from the Replies table."

    def handle(self, **options):
        """
        This gets cached in Redis as a sorted list of contributors, stored as JSON.

        Example Top Contributor data:

        [
            {
                'twitter_username': 'username1',
                'avatar': 'http://twitter.com/path/to/the/avatar.png',
                'avatar_https': 'https://twitter.com/path/to/the/avatar.png',
                'all': 5211,
                '1m': 230,
                '1w': 33,
                '1d': 3,
            },
            { ... },
            { ... },
        ]
        """
        if settings.STAGE:
            return

        contributor_stats = {}

        now = datetime.now()
        one_month_ago = now - timedelta(days=30)
        one_week_ago = now - timedelta(days=7)
        yesterday = now - timedelta(days=1)

        for chunk in chunked(Reply.objects.all(), 2500, Reply.objects.count()):
            for reply in chunk:
                user = reply.twitter_username
                if user not in contributor_stats:
                    raw = json.loads(reply.raw_json)
                    if "from_user" in raw:  # For tweets collected using v1 API
                        user_data = raw
                    else:
                        user_data = raw["user"]

                    contributor_stats[user] = {
                        "twitter_username": user,
                        "avatar": user_data["profile_image_url"],
                        "avatar_https": user_data["profile_image_url_https"],
                        "all": 0,
                        "1m": 0,
                        "1w": 0,
                        "1d": 0,
                    }
                contributor = contributor_stats[reply.twitter_username]

                contributor["all"] += 1
                if reply.created > one_month_ago:
                    contributor["1m"] += 1
                    if reply.created > one_week_ago:
                        contributor["1w"] += 1
                        if reply.created > yesterday:
                            contributor["1d"] += 1

        sort_key = settings.CC_TOP_CONTRIB_SORT
        limit = settings.CC_TOP_CONTRIB_LIMIT
        # Sort by whatever is in settings, break ties with 'all'
        contributor_stats = sorted(
            list(contributor_stats.values()), key=lambda c: (c[sort_key], c["all"]), reverse=True,
        )[:limit]

        try:
            redis = redis_client(name="default")
            key = settings.CC_TOP_CONTRIB_CACHE_KEY
            redis.set(key, json.dumps(contributor_stats))
        except RedisError as e:
            log.error("Redis error: %s" % e)

        return contributor_stats
