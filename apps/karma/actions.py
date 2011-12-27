from datetime import date, datetime

from django.contrib.auth.models import User

from celery.decorators import task
from statsd import statsd
import waffle

from karma.manager import KarmaManager


class KarmaAction(object):
    """Abstract base class for karma actions."""
    action_type = None  # For example 'first-answer'.
    points = 0  # Number of points the action is worth.

    def __init__(self, user, day=date.today()):
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

    def save(self, async=True, redis=None):
        """Save the action information to redis.

        :arg async: save in a celery task
        :arg redis: used by init task to reuse the redis connection
        """
        if waffle.switch_is_active('karma'):
            if async:
                self._save.delay(self)
            else:
                # Passing self below is required because the method is a @task
                self._save(self, redis)

    def delete(self, async=True):
        """Remove an action from redis.

        :arg async: save in a celery task
        """
        if waffle.switch_is_active('karma'):
            if async:
                self._delete.delay(self)
            else:
                # Passing self below is required because the method is a @task
                self._delete(self)

    @task
    def _save(self, redis=None):
        statsd.incr('karma.{t}'.format(t=self.action_type))
        KarmaManager(redis).save_action(self)

    @task
    def _delete(self):
        statsd.incr('karma.delete.{t}'.format(t=self.action_type))
        KarmaManager().delete_action(self)
