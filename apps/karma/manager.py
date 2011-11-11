from datetime import date, timedelta
import logging

from django.contrib.auth.models import User

from redis.exceptions import ConnectionError

from sumo.decorators import for_all_methods
from sumo.redis_utils import redis_client, RedisError


KEY_PREFIX = 'karma'  # Prefix for the Redis keys used.

log = logging.getLogger('k.karma')


def _handle_redis_errors(func):
    """Decorator for KarmaManager methods.

    It handles configuration and connection errors.
    """
    def wrapper(*args, **kwargs):
        if not args[0].redis:
            return None

        try:
            return func(*args, **kwargs)
        except ConnectionError as e:
            log.error('Redis connection error: %s' % e)
            return None
    return wrapper


@for_all_methods(_handle_redis_errors)
class KarmaManager(object):
    """Manager for querying karma data in Redis."""
    def __init__(self, redis=None):
        if not redis:
            try:
                redis = redis_client(name='karma')
            except RedisError as e:
                log.error('Redis error: %s' % e)
        self.redis = redis

    # Setters:
    def save_action(self, action):
        """Save a new karma action to redis."""
        key = hash_key(action.userid)

        # Point counters:
        # Increment total points
        self.redis.hincrby(key, 'points:total', action.points)
        # Increment points daily count
        self.redis.hincrby(key, 'points:{d}'.format(
            d=action.date), action.points)
        # Increment points monthly count
        self.redis.hincrby(key, 'points:{y}-{m:02d}'.format(
            y=action.date.year, m=action.date.month), action.points)
        # Increment points yearly count
        self.redis.hincrby(key, 'points:{y}'.format(
            y=action.date.year), action.points)

        # Action counters:
        # Increment action total count
        self.redis.hincrby(key, '{t}:total'.format(t=action.action_type), 1)
        # Increment action daily count
        self.redis.hincrby(key, '{t}:{d}'.format(
             t=action.action_type, d=action.date), 1)
        # Increment action monthly count
        self.redis.hincrby(key, '{t}:{y}-{m:02d}'.format(
            t=action.action_type, y=action.date.year, m=action.date.month), 1)
        # Increment action yearly count
        self.redis.hincrby(key, '{t}:{y}'.format(
            t=action.action_type, y=action.date.year), 1)

    # TODO: When updating lists, create a new list with temporary name,
    # then rename it to the canonical list.
    def update_top_alltime(self):
        """Updated the top contributors alltime sorted set."""
        # Update sorted set
        key = '{p}:points:total'.format(p=KEY_PREFIX)
        # TODO: Stop loading the full user list like this
        for userid in User.objects.values_list('id', flat=True):
            pts = self.total_points(userid)
            if pts:
                self.redis.zadd(key, userid, pts)

    def update_top_week(self):
        """Updated the top contributors past week sorted set."""
        # Update sorted set
        key = '{p}:points:week'.format(p=KEY_PREFIX)
        # TODO: Stop loading the full user list like this
        for userid in User.objects.values_list('id', flat=True):
            pts = self.week_points(userid)
            if pts:
                self.redis.zadd(key, userid, pts)

    def recalculate_points(self, user, actions):
        """Recalculate the points for a given user.

        `actions` is a dict that maps action types to points."""
        # TODO: think about having a register mechanism so KarmaManager can
        # know about all the (registered) actions.
        key = hash_key(user)
        values = self.user_data(user)

        # Remove existing point values
        point_keys = [k for k in values.keys() if k.startswith('points:')]
        for k in point_keys:
            values.pop(k)
            self.redis.hdel(key, k)
            # TODO: Redis v2.4.x allows deleting multiple keys in one call.

        # Recalculate all the points
        for k in values:
            action_type, action_date = k.split(':')
            points = actions[action_type] * int(values[k])
            self.redis.hincrby(key, 'points:{d}'.format(
                d=action_date), points)

    # Getters:
    def top_alltime(self, count=10, offset=0):
        """Returns the top users based on alltime points."""
        return self._top_points(count, offset, 'total')

    def top_week(self, count=10, offset=0):
        """Returns the top users based on points in the last 7 days."""
        return self._top_points(count, offset, 'week')

    def _top_points(self, count, offset, suffix):
        ids = self.redis.zrevrange('{p}:points:{s}'.format(
            p=KEY_PREFIX, s=suffix), offset, offset + count - 1)
        users = list(User.objects.filter(id__in=ids))
        users.sort(key=lambda user: ids.index(str(user.id)))
        return users

    def ranking_alltime(self, user):
        """The user's alltime ranking."""
        if not self.total_points(user):
            return None
        return self.redis.zrevrank('{p}:points:total'.format(p=KEY_PREFIX),
                                   userid(user)) + 1

    def ranking_week(self, user):
        """The user's ranking for last 7 days"""
        if not self.week_points(user):
            return None
        return self.redis.zrevrank('{p}:points:week'.format(p=KEY_PREFIX),
                                   userid(user)) + 1

    def total_points(self, user):
        """Returns the total points for a given user."""
        count = self.redis.hget(hash_key(user), 'points:total')
        return int(count) if count else 0

    def week_points(self, user):
        """Returns total points from the last 7 days for a given user."""
        today = date.today()
        days = [today - timedelta(days=d + 1) for d in range(7)]
        counts = self.redis.hmget(hash_key(user),
                                  ['points:{d}'.format(d=d) for d in days])
        fn = lambda x: int(x) if x else 0
        count = sum([fn(c) for c in counts])
        return count

    def daily_points(self, user, days_back=30):
        """Returns a list of points from the past `days_back` days."""
        today = date.today()
        days = [today - timedelta(days=d) for d in range(days_back)]
        counts = self.redis.hmget(hash_key(user),
                                  ['points:{d}'.format(d=d) for d in days])
        fn = lambda x: int(x) if x else 0
        return [fn(c) for c in counts]

    def monthly_points(self, user, months_back=12):
        """Returns a list of points from the past `months_back` months."""
        # TODO: probably needed for graphing
        pass

    def total_count(self, action, user):
        """Returns the total count of an action for a given user."""
        count = self.redis.hget(
            hash_key(user), '{t}:total'.format(t=action.action_type))
        return int(count) if count else 0

    def day_count(self, action, user, date=date.today()):
        """Returns the total count of an action for a given user and day."""
        count = self.redis.hget(
            hash_key(user), '{t}:{d}'.format(d=date, t=action.action_type))
        return int(count) if count else 0

    def week_count(self, action, user):
        """Returns total count of an action for a given user (last 7 days)."""
        # TODO: DRY this up with week_points and daily_points.
        today = date.today()
        days = [today - timedelta(days=d + 1) for d in range(7)]
        counts = self.redis.hmget(hash_key(user), ['{t}:{d}'.format(
            t=action.action_type, d=d) for d in days])
        fn = lambda x: int(x) if x else 0
        count = sum([fn(c) for c in counts])
        return count

    def month_count(self, action, user, year, month):
        """Returns the total count of an action for a given user and month."""
        count = self.redis.hget(
            hash_key(user),
            '{t}:{y}-{m:02d}'.format(t=action.action_type, y=year, m=month))
        return int(count) if count else 0

    def year_count(self, action, user, year):
        """Returns the total count of an action for a given user and year."""
        count = self.redis.hget(
            hash_key(user), '{t}:{y}'.format(y=year, t=action.action_type))
        return int(count) if count else 0

    def user_data(self, user):
        """Returns all the data stored for the given user."""
        return self.redis.hgetall(hash_key(user))


def hash_key(user):
    """Returns the hash key for a given user."""
    return "{p}:{u}".format(p=KEY_PREFIX, u=userid(user))


def userid(user):
    if isinstance(user, User):
        return user.id
    else:
        return user
