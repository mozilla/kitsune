from datetime import date
import mock
from nose import SkipTest
from nose.tools import eq_
import waffle

from karma.actions import KarmaAction
from karma.manager import KarmaManager
from sumo.tests import TestCase
from sumo.utils import redis_client
from users.tests import user


class TestAction1(KarmaAction):
    """A test action for testing!"""
    action_type = 'test-action-1'
    points = 3


class TestAction2(KarmaAction):
    """Another test action for testing!"""
    action_type = 'test-action-2'
    points = 7


class KarmaActionTests(TestCase):
    def setUp(self):
        super(KarmaActionTests, self).setUp()
        self.user = user(save=True)
        try:
            self.mgr = KarmaManager()
            redis_client('karma').flushdb()
        except (KeyError, AttributeError):
            raise SkipTest

    @mock.patch.object(waffle, 'switch_is_active')
    def test_action(self, switch_is_active):
        """Save an action and verify."""
        switch_is_active.return_value = True
        TestAction1(user=self.user).save()
        eq_(3, self.mgr.total_points(self.user))
        eq_(1, self.mgr.total_count(TestAction1, self.user))
        today = date.today()
        eq_(1, self.mgr.day_count(TestAction1, self.user, today))
        eq_(1, self.mgr.month_count(TestAction1, self.user, today.year,
                                    today.month))
        eq_(1, self.mgr.year_count(TestAction1, self.user, today.year))

    @mock.patch.object(waffle, 'switch_is_active')
    def test_two_actions(self, switch_is_active):
        """Save two actions, one twice, and verify."""
        switch_is_active.return_value = True
        TestAction1(user=self.user).save()
        TestAction2(user=self.user).save()
        TestAction2(user=self.user).save()
        eq_(17, self.mgr.total_points(self.user))
        eq_(1, self.mgr.total_count(TestAction1, self.user))
        eq_(2, self.mgr.total_count(TestAction2, self.user))
        today = date.today()
        eq_(1, self.mgr.day_count(TestAction1, self.user, today))
        eq_(1, self.mgr.month_count(TestAction1, self.user, today.year,
                                    today.month))
        eq_(1, self.mgr.year_count(TestAction1, self.user, today.year))
        eq_(2, self.mgr.day_count(TestAction2, self.user, today))
        eq_(2, self.mgr.month_count(TestAction2, self.user, today.year,
                                    today.month))
        eq_(2, self.mgr.year_count(TestAction2, self.user, today.year))
