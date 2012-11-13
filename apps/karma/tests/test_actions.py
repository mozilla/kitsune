from datetime import date

import mock
from nose import SkipTest
from nose.tools import eq_
import waffle

from karma.manager import KarmaManager
from karma.tests import TestAction1, TestAction2
from sumo.redis_utils import redis_client, RedisError
from sumo.tests import TestCase
from users.tests import user


class KarmaActionTests(TestCase):
    def setUp(self):
        super(KarmaActionTests, self).setUp()
        self.user = user(save=True)
        try:
            self.mgr = KarmaManager()
            redis_client('karma').flushdb()
        except RedisError:
            raise SkipTest

    @mock.patch.object(waffle, 'switch_is_active')
    def test_action(self, switch_is_active):
        """Save an action and verify."""
        switch_is_active.return_value = True
        TestAction1(user=self.user).save()
        eq_(3, self.mgr.count('all', self.user, type='points'))
        eq_(1, self.mgr.count('all', self.user, type=TestAction1.action_type))
        today = date.today()
        eq_(1, self.mgr.day_count(self.user, today, TestAction1.action_type))
        eq_(1, self.mgr.month_count(self.user, today.year,
                                    today.month, TestAction1.action_type))
        eq_(1, self.mgr.year_count(self.user, today.year,
                                   TestAction1.action_type))

    @mock.patch.object(waffle, 'switch_is_active')
    def test_two_actions(self, switch_is_active):
        """Save two actions, one twice, and verify."""
        switch_is_active.return_value = True
        TestAction1(user=self.user).save()
        TestAction2(user=self.user).save()
        TestAction2(user=self.user).save()
        eq_(17, self.mgr.count('all', self.user, type='points'))
        eq_(1, self.mgr.count('all', self.user, type=TestAction1.action_type))
        eq_(2, self.mgr.count('all', self.user, type=TestAction2.action_type))
        today = date.today()
        eq_(1, self.mgr.day_count(self.user, today, TestAction1.action_type))
        eq_(1, self.mgr.month_count(self.user, today.year, today.month,
                                    TestAction1.action_type))
        eq_(1, self.mgr.year_count(self.user, today.year,
                                   TestAction1.action_type))
        eq_(2, self.mgr.day_count(self.user, today, TestAction2.action_type))
        eq_(2, self.mgr.month_count(self.user, today.year, today.month,
                                    TestAction2.action_type))
        eq_(2, self.mgr.year_count(self.user, today.year,
                                   TestAction2.action_type))

    @mock.patch.object(waffle, 'switch_is_active')
    def test_delete_action(self, switch_is_active):
        """Save two actions, one twice, and verify."""
        switch_is_active.return_value = True
        today = date.today()

        # Create two TestAction1s and verify counts.
        TestAction1(user=self.user).save()
        TestAction1(user=self.user).save()
        eq_(6, self.mgr.count('all', self.user, type='points'))
        eq_(2, self.mgr.count('all', self.user, type=TestAction1.action_type))
        today = date.today()
        eq_(2, self.mgr.day_count(self.user, today, TestAction1.action_type))
        eq_(2, self.mgr.month_count(self.user, today.year,
                                    today.month, TestAction1.action_type))
        eq_(2, self.mgr.year_count(self.user, today.year,
                                   TestAction1.action_type))

        # Delete one and verify new counts
        TestAction1(user=self.user).delete()
        eq_(3, self.mgr.count('all', self.user, type='points'))
        eq_(1, self.mgr.count('all', self.user, type=TestAction1.action_type))
        today = date.today()
        eq_(1, self.mgr.day_count(self.user, today, TestAction1.action_type))
        eq_(1, self.mgr.month_count(self.user, today.year,
                                    today.month, TestAction1.action_type))
        eq_(1, self.mgr.year_count(self.user, today.year,
                                   TestAction1.action_type))

        # Delete the other and verify all zeroes
        TestAction1(user=self.user).delete()
        eq_(0, self.mgr.count('all', self.user, type='points'))
        eq_(0, self.mgr.count('all', self.user, type=TestAction1.action_type))
        today = date.today()
        eq_(0, self.mgr.day_count(self.user, today, TestAction1.action_type))
        eq_(0, self.mgr.month_count(self.user, today.year,
                                    today.month, TestAction1.action_type))
        eq_(0, self.mgr.year_count(self.user, today.year,
                                   TestAction1.action_type))
