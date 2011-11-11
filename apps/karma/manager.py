from datetime import date, timedelta
import logging

from django.contrib.auth.models import User

from redis.exceptions import ConnectionError

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


class KarmaManager(object):
    """Manager for querying karma data in Redis."""

    date_ranges = {'1w': 7, '1m': 30, '3m': 91, '6m': 182, '1y': 365}
    action_types = {}

    def __init__(self, redis=None):
        if not redis:
            try:
                redis = redis_client(name='karma')
            except RedisError as e:
                log.error('Redis error: %s' % e)
        self.redis = redis

    @classmethod
    def register(cls, action):
        cls.action_types[action.action_type] = action.points

    # Setters:
    def save_action(self, action):
        """Save a new karma action to redis."""
        key = hash_key(action.userid)

        # Keep a list of users with karma
        self.redis.sadd('{p}:users'.format(p=KEY_PREFIX), action.userid)

        # Point counters:
        # Increment total points
        self.redis.hincrby(key, 'points:all', action.points)
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
        self.redis.hincrby(key, '{t}:all'.format(t=action.action_type), 1)
        # Increment action daily count
        self.redis.hincrby(key, '{t}:{d}'.format(
             t=action.action_type, d=action.date), 1)
        # Increment action monthly count
        self.redis.hincrby(key, '{t}:{y}-{m:02d}'.format(
            t=action.action_type, y=action.date.year, m=action.date.month), 1)
        # Increment action yearly count
        self.redis.hincrby(key, '{t}:{y}'.format(
            t=action.action_type, y=action.date.year), 1)

    def update_top(self):
        """Update the aggregates and indexes for all actions and ranges."""
        for action_type in self.action_types.keys() + ['points']:
            for daterange in self.date_ranges.keys() + ['all']:
                self._update_top(daterange, action_type)

    def _update_top(self, daterange, type):
        """Update the aggregates and indexes for the given type and range."""
        key = '{p}:{t}:{r}'.format(p=KEY_PREFIX, t=type, r=daterange)
        temp_key = key + ':tmp'
        index_created = False

        for userid in self.user_ids():
            if daterange == 'all':
                # '*:all' is always up to date
                pts = self.count(userid, daterange='all', type=type)
            else:
                # Needs recalculating
                pts = self._count(userid, daterange=daterange, type=type)
                self._set_or_del_hash(userid,
                                      '{t}:{r}'.format(t=type, r=daterange),
                                      pts)

            if pts:
                self.redis.zadd(temp_key, userid, pts)
                index_created = True

        if index_created:
            self.redis.rename(temp_key, key)
        else:
            self.redis.delete(key)

    def _set_or_del_hash(self, userid, key, pts):
        if pts:
            self.redis.hset(hash_key(userid), key, pts)
        else:
            self.redis.hdel(hash_key(userid), key)

    def recalculate_points(self, user):
        """Recalculate the points for a given user."""
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
            points = self.action_types[action_type] * int(values[k])
            self.redis.hincrby(key, 'points:{d}'.format(
                d=action_date), points)

    # Getters:
    @_handle_redis_errors
    def top_users(self, daterange='all', type='points', count=10, offset=0):
        """Get a list of users sorted for the specified range and type."""
        ids = self.top_users_ids(daterange, type, count, offset)
        users = list(User.objects.filter(id__in=ids))
        users.sort(key=lambda user: ids.index(str(user.id)))
        return users

    def top_users_ids(self, daterange='all', type='points', count=10,
                      offset=0):
        """Get a list of user ids sorted for the specified range and type."""
        return self.redis.zrevrange('{p}:{t}:{s}'.format(
            p=KEY_PREFIX, t=type, s=daterange), offset, offset + count - 1)

    @_handle_redis_errors
    def ranking(self, user, daterange='all', type='points'):
        """The user's ranking for the given range and type."""
        if not self.count(user=user, daterange=daterange, type=type):
            return None
        return self.redis.zrevrank('{p}:{t}:{r}'.format(
            p=KEY_PREFIX, t=type, r=daterange), userid(user)) + 1

    def count(self, user, daterange='all', type='points'):
        """The user's count for the given range and type."""
        count = self.redis.hget(hash_key(user),
                                '{t}:{r}'.format(t=type, r=daterange))
        return int(count) if count else 0

    def daily_counts(self, user, daterange='all', type='points'):
        """Return a list of counts per day for the give range and type."""
        today = date.today()
        num_days = self.date_ranges[daterange]
        days = [today - timedelta(days=d) for d in range(num_days)]
        counts = self.redis.hmget(
            hash_key(user), ['{t}:{d}'.format(t=type, d=d) for d in days])
        fn = lambda x: int(x) if x else 0
        return [fn(c) for c in counts]

    def day_count(self, user, date=date.today(), type='points'):
        """Returns the total count for given type, user and day."""
        count = self.redis.hget(
            hash_key(user), '{t}:{d}'.format(d=date, t=type))
        return int(count) if count else 0

    def month_count(self, user, year, month, type='points'):
        """Returns the total countfor given type, user and moth."""
        count = self.redis.hget(
            hash_key(user),
            '{t}:{y}-{m:02d}'.format(t=type, y=year, m=month))
        return int(count) if count else 0

    def year_count(self, user, year, type='points'):
        """Returns the total count for given type, user and year."""
        count = self.redis.hget(
            hash_key(user), '{t}:{y}'.format(y=year, t=type))
        return int(count) if count else 0

    def user_data(self, user):
        """Returns all the data stored for the given user."""
        return self.redis.hgetall(hash_key(user))

    def user_ids(self):
        """Return the user ids of all users with karma activity."""
        return self.redis.smembers('{p}:users'.format(p=KEY_PREFIX))

    def _count(self, user, daterange, type='points'):
        """Calculates a user's count for range and type from daily counts."""
        daily_counts = self.daily_counts(user=user, daterange=daterange,
                                         type=type)
        return sum(daily_counts)


def hash_key(user):
    """Returns the hash key for a given user."""
    return "{p}:{u}".format(p=KEY_PREFIX, u=userid(user))


def userid(user):
    if isinstance(user, User):
        return user.id
    else:
        return user
