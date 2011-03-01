from nose.tools import eq_

from notifications.models import WatchFilter, EmailUser
from notifications.tests import watch_filter
from sumo.tests import TestCase


# TODO: write a test to ensure that event types don't collide
# case-insensitive-ly
# E.g. No duplicates in this list: [et.lower() for et in EVENT_TYPES]


class WatchFilterTests(TestCase):
    """Tests for WatchFilter"""

    def test_value_range(self):
        """Assert 0 and 2**32-1 both fit in the value field.

        That's the range of our hash function.

        """
        MAX_INT = 2 ** 32 - 1
        watch_filter(name='maxint', value=MAX_INT).save()
        eq_(MAX_INT, WatchFilter.objects.get(name='maxint').value)


class EmailUserTests(TestCase):
    """Tests for EmailUser class"""

    def test_blank_username(self):
        """Assert EmailUsers' username is ''.

        This isn't covered by the tests in django.contrib.auth, and we need to
        hear about it if it changes, as some implementations of _mails() depend
        on it.

        """
        eq_('', EmailUser().username)
