import mock
from nose.tools import eq_, ok_

from rest_framework.test import APIClient

from kitsune.sumo.tests import TestCase
from kitsune.notifications import api
from kitsune.users.tests import profile, user
from kitsune.sumo.urlresolvers import reverse


class TestPushNotificationRegistrationSerializer(TestCase):

    def setUp(self):
        self.profile = profile()
        self.user = self.profile.user
        self.request = mock.Mock()
        self.request.user = self.user
        self.context = {
            'request': self.request,
        }
        self.data = {
            'creator': self.user,
            'push_url': 'https://example.com/notifications/123123123',
        }

    def test_automatic_creator(self):
        del self.data['creator']
        serializer = api.PushNotificationRegistrationSerializer(
            context=self.context, data=self.data)
        ok_(serializer.is_valid())
        eq_(serializer.errors, {})
        eq_(serializer.object.creator, self.user)

    def test_cant_register_for_other_users(self):
        wrong_user = user(save=True)
        self.data['creator'] = wrong_user
        serializer = api.PushNotificationRegistrationSerializer(
            context=self.context, data=self.data)
        ok_(not serializer.is_valid())
        eq_(serializer.errors, {
            'creator': ["Can't register push notifications for another user."],
        })
