from datetime import datetime, timedelta
import json

import mock
from nose import SkipTest
from nose.tools import eq_
import waffle

from kitsune.karma import models
from kitsune.karma.manager import KarmaManager
from kitsune.karma.tests import TestAction1, TestAction2
from kitsune.questions.tests import answer
from kitsune.sumo.helpers import urlparams
from kitsune.sumo.redis_utils import redis_client, RedisError
from kitsune.sumo.tests import TestCase, LocalizingClient
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import user, add_permission


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
        add_permission(self.user1, models.Title, 'view_dashboard')

    @mock.patch.object(waffle, 'switch_is_active')
    def test_user_api_no_permission(self, switch_is_active):
        """No view_dashboard permission? No API for you."""
        switch_is_active.return_value = True
        self.client.login(username=self.user2.username, password='testpass')
        url = reverse('karma.api.users')
        response = self.client.get(url)
        eq_(403, response.status_code)

    @mock.patch.object(waffle, 'switch_is_active')
    def test_user_api_default(self, switch_is_active):
        """Test user API with all defaults."""
        switch_is_active.return_value = True
        url = reverse('karma.api.users')
        response = self.client.get(url)
        eq_(200, response.status_code)
        r = json.loads(response.content)
        user_ids = [u[0] for u in r['results']]
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
        user_ids = [u[0] for u in r['results']]
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
        user_ids = [u[0] for u in r['results']]
        eq_([self.user2.id], user_ids)

    @mock.patch.object(waffle, 'switch_is_active')
    def test_user_api_last_activity(self, switch_is_active):
        """Verify the last activity field."""
        switch_is_active.return_value = True

        now = datetime.now()
        one_day = now - timedelta(days=1)
        two_days = now - timedelta(days=2)

        answer(creator=self.user1, created=now, save=True)
        answer(creator=self.user2, created=one_day, save=True)
        answer(creator=self.user3, created=two_days, save=True)

        url = reverse('karma.api.users')
        response = self.client.get(url)
        eq_(200, response.status_code)
        r = json.loads(response.content)
        days_since_last_activity = [u[2] for u in r['results']]
        eq_([1, 2, 0], days_since_last_activity)

    @mock.patch.object(waffle, 'switch_is_active')
    def test_overview_api(self, switch_is_active):
        """Test overview API."""
        switch_is_active.return_value = True
        url = reverse('karma.api.overview')
        url = urlparams(url, daterange='6m')
        response = self.client.get(url)
        eq_(200, response.status_code)
        r = json.loads(response.content)
        overview = r['overview']
        eq_(4, overview['test-action-1'])
        eq_(2, overview['test-action-2'])
