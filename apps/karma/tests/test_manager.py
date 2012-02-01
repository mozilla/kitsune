from datetime import date, timedelta

import mock
from nose import SkipTest
from nose.tools import eq_
import waffle

from karma.manager import KarmaManager
from karma.models import Points
from karma.tests import TestAction1, TestAction2
from sumo.redis_utils import redis_client, RedisError
from sumo.tests import TestCase
from users.tests import user


class KarmaManagerTests(TestCase):
    @mock.patch.object(waffle, 'switch_is_active')
    def setUp(self, switch_is_active):
        switch_is_active.return_value = True

        super(KarmaManagerTests, self).setUp()

        try:
            self.mgr = KarmaManager()
            redis_client('karma').flushdb()
        except RedisError:
            raise SkipTest

        self.user1 = user(save=True)
        self.user2 = user(save=True)
        self.user3 = user(save=True)

        today = date.today()

        # user1 actions (3 + 3 + 7):
        TestAction1(user=self.user1, day=today).save()
        TestAction1(user=self.user1, day=today).save()
        TestAction2(user=self.user1, day=today).save()

        # user2 actions (3 + 7 + 7):
        TestAction1(user=self.user2, day=today - timedelta(days=8)).save()
        TestAction2(user=self.user2, day=today - timedelta(days=32)).save()
        TestAction2(user=self.user2, day=today - timedelta(days=360)).save()

        # user3 actions (3 + 3 + 3 + 7):
        TestAction1(user=self.user3, day=today - timedelta(days=10)).save()
        TestAction1(user=self.user3, day=today - timedelta(days=40)).save()
        TestAction1(user=self.user3, day=today - timedelta(days=190)).save()
        TestAction2(user=self.user3, day=today - timedelta(days=3)).save()

    @mock.patch.object(waffle, 'switch_is_active')
    def test_count(self, switch_is_active):
        """Test count method."""
        switch_is_active.return_value = True
        self.mgr.update_top()
        eq_(13, self.mgr.count(self.user1, type='points'))
        eq_(2, self.mgr.count(self.user1, type=TestAction1.action_type))
        eq_(1, self.mgr.count(self.user1, type=TestAction2.action_type))
        eq_(0, self.mgr.count(self.user2, type='points', daterange='1w'))
        eq_(3, self.mgr.count(self.user2, type='points', daterange='1m'))
        eq_(2, self.mgr.count(self.user2, type=TestAction2.action_type,
                              daterange='1y'))
        eq_(2, self.mgr.count(self.user3, type=TestAction1.action_type,
                              daterange='6m'))

    @mock.patch.object(waffle, 'switch_is_active')
    def test_top_users(self, switch_is_active):
        """Test top_users method."""
        switch_is_active.return_value = True
        self.mgr.update_top()
        u1, u2, u3 = self.user1, self.user2, self.user3
        eq_([u2, u3, u1], self.mgr.top_users())
        eq_([u3, u1, u2], self.mgr.top_users(type=TestAction1.action_type))
        eq_([u3, u1, u2], self.mgr.top_users(type=TestAction1.action_type))
        eq_([u1], self.mgr.top_users(type=TestAction1.action_type,
                                     daterange='1w'))
        eq_([u1, u3], self.mgr.top_users(daterange='1w'))

    @mock.patch.object(waffle, 'switch_is_active')
    def test_ranking(self, switch_is_active):
        """Test ranking method."""
        switch_is_active.return_value = True
        self.mgr.update_top()
        eq_(1, self.mgr.ranking(self.user2))
        eq_(3, self.mgr.ranking(self.user1))
        eq_(1, self.mgr.ranking(self.user1, daterange='1w'))
        eq_(1, self.mgr.ranking(self.user3, type=TestAction1.action_type))

    @mock.patch.object(waffle, 'switch_is_active')
    def test_recalculate_points(self, switch_is_active):
        """Test the recalculate_points method."""
        switch_is_active.return_value = True

        # Create Points with new point values.
        p1 = Points.objects.create(action='test-action-1', points=15)
        Points.objects.create(action='test-action-2', points=12)

        self.mgr.recalculate_points(self.user1)
        eq_(42, self.mgr.count(self.user1, type='points'))

        # Update one of the Point values.
        p1.points = 30
        p1.save()

        self.mgr.recalculate_points(self.user1)
        eq_(72, self.mgr.count(self.user1, type='points'))

    @mock.patch.object(waffle, 'switch_is_active')
    def test_overview_counts(self, switch_is_active):
        """Verify the overview counts are correct."""
        switch_is_active.return_value = True
        self.mgr.update_top()
        eq_(46, self.mgr.count(type='points'))
        eq_(6, self.mgr.count(type=TestAction1.action_type))
        eq_(4, self.mgr.count(type=TestAction2.action_type))
        eq_(2, self.mgr.count(type=TestAction1.action_type, daterange='1w'))
        eq_(2, self.mgr.count(type=TestAction2.action_type, daterange='1m'))
        eq_(3, self.mgr.count(type=TestAction2.action_type, daterange='6m'))
        eq_(2, self.mgr.day_count(type=TestAction1.action_type))
        eq_(1, self.mgr.day_count(type=TestAction2.action_type))
