from datetime import date, datetime, timedelta

from django.contrib.auth.models import User

from celery.decorators import task
import waffle

from sumo.utils import redis_client


KEY_PREFIX = 'karma'  # Prefix for the Redis keys used.


class KarmaAction(object):
    """Abstract base class for karma actions."""
    action_type = None  # For example 'first-answer'.
    points = 0  # Number of points the action is worth.

    def __init__(self, user, day=date.today(), redis=None):
        if not waffle.switch_is_active('karma'):
            return
        if isinstance(user, User):
            self.userid = user.id
        else:
            self.userid = user
        if isinstance(day, datetime):  # Gracefully handle a datetime.
            self.date = day.date()
        else:
            self.date = day
        if not redis:
            self.redis = redis_client(name='karma')
        else:
            self.redis = redis

    def save(self):
        """Save the action information to redis."""
        if waffle.switch_is_active('karma'):
            self._save.delay(self)

    @task
    def _save(self):
        key = hash_key(self.userid)

        # Point counters:
        # Increment total points
        self.redis.hincrby(key, 'points:total', self.points)
        # Increment points daily count
        self.redis.hincrby(key, 'points:{d}'.format(
            d=self.date), self.points)
        # Increment points monthly count
        self.redis.hincrby(key, 'points:{y}-{m:02d}'.format(
            y=self.date.year, m=self.date.month), self.points)
        # Increment points yearly count
        self.redis.hincrby(key, 'points:{y}'.format(
            y=self.date.year), self.points)

        # Action counters:
        # Increment action total count
        self.redis.hincrby(key, '{t}:total'.format(t=self.action_type), 1)
        # Increment action daily count
        self.redis.hincrby(key, '{t}:{d}'.format(
             t=self.action_type, d=self.date), 1)
        # Increment action monthly count
        self.redis.hincrby(key, '{t}:{y}-{m:02d}'.format(
            t=self.action_type, y=self.date.year, m=self.date.month), 1)
        # Increment action yearly count
        self.redis.hincrby(key, '{t}:{y}'.format(
            t=self.action_type, y=self.date.year), 1)


# TODO: move this to it's own file?
class KarmaManager(object):
    """Manager for querying karma data in Redis."""
    def __init__(self):
        self.redis = redis_client(name='karma')

    # Updaters:
    def update_top_alltime(self):
        """Updated the top contributors alltime sorted set."""
        key = '{p}:points:total'.format(p=KEY_PREFIX)
        # TODO: Maintain a user id list in Redis?
        for userid in User.objects.values_list('id', flat=True):
            pts = self.total_points(userid)
            if pts:
                self.redis.zadd(key, userid, pts)

    def update_top_week(self):
        """Updated the top contributors past week sorted set."""
        key = '{p}:points:week'.format(p=KEY_PREFIX)
        for userid in User.objects.values_list('id', flat=True):
            pts = self.week_points(userid)
            if pts:
                self.redis.zadd(key, userid, pts)

    # def update_trending...

    # Getters:
    def top_alltime(self, count=10):
        """Returns the top users based on alltime points."""
        return self._top_points(count, 'total')

    def top_week(self, count=10):
        """Returns the top users based on points in the last 7 days."""
        return self._top_points(count, 'week')

    def _top_points(self, count, suffix):
        ids = self.redis.zrevrange('{p}:points:{s}'.format(
            p=KEY_PREFIX, s=suffix), 0, count - 1)
        users = list(User.objects.filter(id__in=ids))
        users.sort(key=lambda user: ids.index(str(user.id)))
        return users

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
        # TODO: Tricky?
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
    if isinstance(user, User):
        userid = user.id
    else:
        userid = user
    return "{p}:{u}".format(p=KEY_PREFIX, u=userid)
