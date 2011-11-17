import json

import mock
from nose import SkipTest
from nose.tools import eq_
import waffle

from karma.manager import KarmaManager
from karma.tests import TestAction1, TestAction2
from sumo.helpers import urlparams
from sumo.redis_utils import redis_client, RedisError
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.tests import user


class KarmaAPITests(TestCase):
    client_class = LocalizingClient

    @mock.patch.object(waffle, 'switch_is_active')
    def setUp(self, switch_is_active):
        switch_is_active.return_value = True

        super(KarmaAPITests, self).setUp()

        try:
            self.mgr = KarmaManager()
            redis_client('karma').flushdb()
        except RedisError:
            raise SkipTest

        self.user1 = user(save=True)
        self.user2 = user(save=True)
        self.user3 = user(save=True)

        TestAction1(user=self.user1).save()
        TestAction2(user=self.user2).save()
        TestAction2(user=self.user2).save()
        TestAction1(user=self.user3).save()
        TestAction1(user=self.user3).save()
        TestAction1(user=self.user3).save()
        self.mgr.update_top()

        self.client.login(username=self.user1.username, password='testpass')
        # TODO: give the user the right permission when that is setup

    @mock.patch.object(waffle, 'switch_is_active')
    def test_user_api_default(self, switch_is_active):
        """Test user API with all defaults."""
        switch_is_active.return_value = True
        url = reverse('karma.api.users')
        response = self.client.get(url)
        eq_(200, response.status_code)
        r = json.loads(response.content)
        user_ids = [u[0] for u in r['users']]
        eq_([self.user2.id, self.user3.id, self.user1.id], user_ids)

    @mock.patch.object(waffle, 'switch_is_active')
    def test_user_api_sort_testaction1(self, switch_is_active):
        """Test user API with sort = TestAction1."""
        switch_is_active.return_value = True
        url = reverse('karma.api.users')
        url = urlparams(url, sort=TestAction1.action_type)
        response = self.client.get(url)
        eq_(200, response.status_code)
        r = json.loads(response.content)
        user_ids = [u[0] for u in r['users']]
        eq_([self.user3.id, self.user1.id], user_ids)

    @mock.patch.object(waffle, 'switch_is_active')
    def test_user_api_sort_testaction2(self, switch_is_active):
        """Test user API with sort = TestAction2."""
        switch_is_active.return_value = True
        url = reverse('karma.api.users')
        url = urlparams(url, sort=TestAction2.action_type)
        response = self.client.get(url)
        eq_(200, response.status_code)
        r = json.loads(response.content)
        user_ids = [u[0] for u in r['users']]
        eq_([self.user2.id], user_ids)
