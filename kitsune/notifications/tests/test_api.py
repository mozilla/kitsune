from datetime import datetime

from actstream.actions import follow
from actstream.signals import action
from actstream.models import Action, Follow
import mock
from nose.tools import eq_, ok_
from rest_framework.test import APIClient

from kitsune.notifications import api
from kitsune.notifications.models import Notification
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.questions.tests import question
from kitsune.users.tests import profile, user


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


class TestNotificationSerializer(TestCase):
    def test_correct_fields(self):
        follower = profile()
        followed = profile()
        q = question(creator=followed.user, save=True)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower.user, followed.user)

        # Make a new action for the above. This should trigger notifications
        action.send(followed.user, verb='asked', action_object=q)
        act = Action.objects.order_by('-id')[0]
        notification = Notification.objects.get(action=act)

        serializer = api.NotificationSerializer(instance=notification)

        eq_(serializer.data['is_read'], False)
        eq_(serializer.data['actor'], {
            'type': 'user',
            'username': followed.user.username,
            'display_name': followed.name
        })
        eq_(serializer.data['verb'], 'asked')
        eq_(serializer.data['action_object'], {
            'type': 'question',
            'id': q.id,
        })
        eq_(serializer.data['target'], None)
        eq_(type(serializer.data['timestamp']), datetime)


class TestNotificationViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()

        follower = profile()
        followed = profile()
        q = question(creator=followed.user, save=True)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()

        follow(follower.user, followed.user)

        # Make a new action for the above. This should trigger notifications
        action.send(followed.user, verb='asked', action_object=q)
        act = Action.objects.order_by('-id')[0]
        self.notification = Notification.objects.get(action=act)

    def test_mark_read(self):
        eq_(self.notification.is_read, False)
        self.client.force_authenticate(user=self.notification.owner)
        req = self.client.post(reverse('notification-mark-read', args=[self.notification.id]))
        eq_(req.status_code, 204)
        n = Notification.objects.get(id=self.notification.id)
        eq_(n.is_read, True)

    def test_mark_unread(self):
        self.notification.is_read = True
        self.notification.save()
        self.client.force_authenticate(user=self.notification.owner)
        req = self.client.post(reverse('notification-mark-unread', args=[self.notification.id]))
        eq_(req.status_code, 204)
        n = Notification.objects.get(id=self.notification.id)
        eq_(n.is_read, False)
