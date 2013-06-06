from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging

from django.contrib.auth.models import User

from redis.exceptions import ConnectionError
from statsd import statsd

from kitsune.sumo.redis_utils import redis_client, RedisError


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
            statsd.incr('redis.errror')
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
                statsd.incr('redis.errror')
                log.error('Redis error: %s' % e)
        self.redis = redis

    @classmethod
    def register(cls, action):
        cls.action_types[action.action_type] = action

    # Setters:
    @_handle_redis_errors
    def save_action(self, action, subtract=False):
        """Save a new karma action to redis.

        :arg action: the action to save
        :arg subract: used by delete_action to subtract instead of add
            to the stats.
        """
        # Keep a list of users with karma
        self.redis.sadd('{p}:users'.format(p=KEY_PREFIX), action.userid)

        if subtract:
            pts_incr = action.points * -1
            count_incr = -1
        else:
            pts_incr = action.points
            count_incr = 1

        # Point counters:
        # Increment user and overview counts
        for key in [hash_key(action.userid), hash_key('overview')]:
            # Increment total points
            self.redis.hincrby(key, 'points:all', pts_incr)
            # Increment points daily count
            self.redis.hincrby(
                key, 'points:{d}'.format(d=action.date), pts_incr)
            # Increment points monthly count
            self.redis.hincrby(key, 'points:{y}-{m:02d}'.format(
                y=action.date.year, m=action.date.month), pts_incr)
            # Increment points yearly count
            self.redis.hincrby(
                key, 'points:{y}'.format(y=action.date.year), pts_incr)

            # Action counters:
            # Increment action total count
            self.redis.hincrby(
                key, '{t}:all'.format(t=action.action_type), count_incr)
            # Increment action daily count
            self.redis.hincrby(key, '{t}:{d}'.format(
                 t=action.action_type, d=action.date), count_incr)
            # Increment action monthly count
            self.redis.hincrby(key, '{t}:{y}-{m:02d}'.format(
                t=action.action_type, y=action.date.year,
                m=action.date.month), count_incr)
            # Increment action yearly count
            self.redis.hincrby(key, '{t}:{y}'.format(
                t=action.action_type, y=action.date.year), count_incr)

    def delete_action(self, action):
        """Back out the stats for an action.

        :arg action: the action to delete
        """
        self.save_action(action, subtract=True)

    def update_top(self):
        """Update the aggregates and indexes for all actions and ranges."""
        for action_type in self.action_types.keys() + ['points']:
            for daterange in self.date_ranges.keys() + ['all']:
                self._update_top(daterange, action_type)

    def _update_top(self, daterange, type):
        """Update the aggregates and indexes for the given type and range."""
        log.info('[karma] Updating %s for %s' % (type, daterange))

        overview_key = hash_key('overview')
        hash_field_key = '{t}:{r}'.format(t=type, r=daterange)
        sset_key = '{p}:{t}:{r}'.format(p=KEY_PREFIX, t=type, r=daterange)
        temp_sset_key = sset_key + ':tmp'
        created = False
        total_count = 0

        for userid in self.user_ids():
            if daterange == 'all':
                # '*:all' is always up to date
                count = self.count('all', userid, type=type)
            else:
                # Needs recalculating
                count = self._count(daterange, userid, type=type)
                self._set_or_del_hash(userid, hash_field_key, count)

            if count:
                self.redis.zadd(temp_sset_key, userid, count)
                total_count += count
                created = True

        # Update the overview (totals) hash.
        self.redis.hset(overview_key, hash_field_key, total_count)

        # Replace the old index with the new one, if we created one.
        # Otherwise, we can delete the old index altogether.
        if created:
            self.redis.rename(temp_sset_key, sset_key)
        else:
            self.redis.delete(sset_key)

        log.info('[karma] Done updating %s for %s' % (type, daterange))

    def _set_or_del_hash(self, userid, key, count):
        if count:
            self.redis.hset(hash_key(userid), key, count)
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
            points = self.action_types[action_type].points * int(values[k])
            self.redis.hincrby(key, 'points:{d}'.format(
                d=action_date), points)

    # Getters:
    @_handle_redis_errors
    def top_users(self, daterange, type='points', count=10, offset=0):
        """Get a list of users sorted for the specified range and type."""
        ids = self.top_users_ids(daterange, type, count, offset)
        users = list(User.objects.filter(id__in=ids))
        users.sort(key=lambda user: ids.index(str(user.id)))
        return users

    def top_users_ids(self, daterange, type='points', count=10,
                      offset=0):
        """Get a list of user ids sorted for the specified range and type."""
        return self.redis.zrevrange('{p}:{t}:{s}'.format(
            p=KEY_PREFIX, t=type, s=daterange), offset, offset + count - 1)

    @_handle_redis_errors
    def ranking(self, daterange, user, type='points'):
        """The user's ranking for the given range and type."""
        if self.count(user=user, daterange=daterange, type=type):
            rank = self.redis.zrevrank('{p}:{t}:{r}'.format(
                p=KEY_PREFIX, t=type, r=daterange), userid(user))
            if rank != None:
                return rank + 1
        return None

    @_handle_redis_errors
    def count(self, daterange='all', user='overview', type='points'):
        """The user's count for the given range and type.

        The default daterange is all time, and the default "user" is 'overview'
        which is an aggregate count over all users.

        There is a default for daterange, unlike elsewhere in this class, so
        that this count() method behaves like a normal Django ORM count method.
        """
        count = self.redis.hget(hash_key(user),
                                '{t}:{r}'.format(t=type, r=daterange))
        return int(count) if count else 0

    def daily_counts(self, daterange, user='overview', type='points',
                     *arg, **kwargs):
        """Return a list of counts per day for the give range and type.

        The default "user" is 'overview' which is an aggregate count
        over all users.
        """
        today = date.today()
        num_days = self.date_ranges[daterange]
        days = [today - timedelta(days=d) for d in range(num_days)][::-1]
        counts = self.redis.hmget(
            hash_key(user), ['{t}:{d}'.format(t=type, d=d) for d in days])
        return [int(c or 0) for c in counts], [d.strftime('%A') for d in days]

    def day_count(self, user='overview', count_date=None, type='points'):
        """Returns the total count for given type, user and day.

        The default "user" is 'overview' which is an aggregate count
        over all users.
        """
        count_date = count_date or date.today()
        count = self.redis.hget(
            hash_key(user), '{t}:{d}'.format(d=count_date, t=type))
        return int(count) if count else 0

    def monthly_counts(self, daterange, userid=None, type='points',
                       *arg, **kwargs):
        daterange = daterange or '1y'
        month_ranges = {'1m': 1, '3m': 3, '6m': 6, '1y': 12}
        num_months = month_ranges[daterange]
        userid = userid or 'overview'
        today = date.today()
        dates = []
        for r in range(-1 * num_months, 0):
            dates.append(today + relativedelta(months=r + 1))
        counts = self.redis.hmget(
            hash_key(userid),
            ['{t}:{y}-{m:02d}'.format(t=type, y=d.year, m=d.month) for
             d in dates])
        return [int(c or 0) for c in counts], [d.strftime('%b') for d in dates]

    def month_count(self, user='overview', year=None,
                    month=None, type='points'):
        """Returns the total countfor given type, user and month.

        The default "user" is 'overview' which is an aggregate count
        over all users.
        """
        year = year or date.today().year
        month = month or date.today().month
        count = self.redis.hget(
            hash_key(user),
            '{t}:{y}-{m:02d}'.format(t=type, y=year, m=month))
        return int(count) if count else 0

    def year_count(self, user='overview', year=date.today().year,
                   type='points'):
        """Returns the total count for given type, user and year.

        The default "user" is 'overview' which is an aggregate count
        over all users.
        """
        count = self.redis.hget(
            hash_key(user), '{t}:{y}'.format(y=year, t=type))
        return int(count) if count else 0

    def user_data(self, user):
        """Returns all the data stored for the given user."""
        return self.redis.hgetall(hash_key(user))

    def user_ids(self):
        """Return the user ids of all users with karma activity."""
        return self.redis.smembers('{p}:users'.format(p=KEY_PREFIX))

    def _count(self, daterange, user, type='points'):
        """Calculates a user's count for range and type from daily counts."""
        daily_counts, days = self.daily_counts(user=user, daterange=daterange,
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
