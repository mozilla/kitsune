import mock
from nose import SkipTest
from nose.tools import eq_
import waffle

from karma.manager import KarmaManager
from karma.tests import TestAction1, TestAction2
from sumo.redis_utils import redis_client, RedisError
from sumo.tests import TestCase
from users.tests import user


class KarmaManagerTests(TestCase):
    def setUp(self):
        super(KarmaManagerTests, self).setUp()
        self.user = user(save=True)
        try:
            self.mgr = KarmaManager()
            redis_client('karma').flushdb()
        except RedisError:
            raise SkipTest

    @mock.patch.object(waffle, 'switch_is_active')
    def test_recalculate_points(self, switch_is_active):
        """Test the recalculate_points method."""
        switch_is_active.return_value = True
        TestAction1(user=self.user).save()  # 3pts
        TestAction1(user=self.user).save()  # 3pts
        TestAction2(user=self.user).save()  # 7pts
        eq_(13, self.mgr.count(self.user, type='points'))
        KarmaManager.action_types = {
            'test-action-1': 15,
            'test-action-2': 12
        }
        self.mgr.recalculate_points(self.user)
        eq_(42, self.mgr.count(self.user, type='points'))
