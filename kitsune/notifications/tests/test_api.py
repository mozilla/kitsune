from datetime import datetime
from unittest.mock import Mock, patch

from actstream.actions import follow
from actstream.models import Action, Follow
from actstream.signals import action
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from kitsune.notifications import api
from kitsune.notifications import tasks as notification_tasks
from kitsune.notifications.models import Notification, RealtimeRegistration
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.templatetags.jinja_helpers import profile_avatar
from kitsune.users.tests import UserFactory


class TestPushNotificationRegistrationSerializer(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = self.user.profile
        self.request = Mock()
        self.request.user = self.user
        self.context = {
            "request": self.request,
        }
        self.data = {
            "creator": self.user,
            "push_url": "https://example.com/notifications/123123123",
        }

    def test_automatic_creator(self):
        del self.data["creator"]
        serializer = api.PushNotificationRegistrationSerializer(
            context=self.context, data=self.data
        )
        assert serializer.is_valid()
        self.assertEqual(serializer.errors, {})
        obj = serializer.save()
        self.assertEqual(obj.creator, self.user)

    def test_cant_register_for_other_users(self):
        wrong_user = UserFactory()
        self.data["creator"] = wrong_user
        serializer = api.PushNotificationRegistrationSerializer(
            context=self.context, data=self.data
        )
        assert not serializer.is_valid()
        self.assertEqual(
            serializer.errors,
            {
                "creator": ["Can't register push notifications for another user."],
            },
        )


class TestNotificationSerializer(TestCase):
    def test_correct_fields(self):
        follower = UserFactory()
        followed = UserFactory()
        q = QuestionFactory(creator=followed)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, followed)

        # Make a new action for the above. This should trigger notifications
        action.send(followed, verb="asked", action_object=q)
        act = Action.objects.order_by("-id")[0]
        notification = Notification.objects.get(action=act)

        serializer = api.NotificationSerializer(instance=notification)

        self.assertEqual(serializer.data["is_read"], False)
        self.assertEqual(
            serializer.data["actor"],
            {
                "type": "user",
                "username": followed.username,
                "display_name": followed.profile.name,
                "avatar": profile_avatar(followed),
            },
        )
        self.assertEqual(serializer.data["verb"], "asked")
        self.assertEqual(serializer.data["action_object"]["type"], "question")
        self.assertEqual(serializer.data["action_object"]["id"], q.id)
        self.assertEqual(serializer.data["target"], None)
        # Check that the serialized data is in the correct format. If it is
        # not, this will throw an exception.
        datetime.strptime(serializer.data["timestamp"], "%Y-%m-%dT%H:%M:%SZ")


class TestNotificationViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.follower = UserFactory()
        self.followed = UserFactory()
        self.question = QuestionFactory(creator=self.followed)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(self.follower, self.followed)

    def _makeNotification(self, is_read=False):
        # Make a new action. This should trigger notifications
        action.send(self.followed, verb="asked", action_object=self.question)
        act = Action.objects.order_by("-id")[0]
        n = Notification.objects.get(action=act)
        if is_read:
            n.is_read = True
            n.save()
        return n

    def test_mark_read(self):
        n = self._makeNotification()
        self.client.force_authenticate(user=self.follower)
        res = self.client.post(reverse("notification-mark-read", args=[n.id]))
        self.assertEqual(res.status_code, 204)
        n = Notification.objects.get(id=n.id)
        self.assertEqual(n.is_read, True)

    def test_mark_unread(self):
        n = self._makeNotification(is_read=True)
        self.client.force_authenticate(user=self.follower)
        res = self.client.post(reverse("notification-mark-unread", args=[n.id]))
        self.assertEqual(res.status_code, 204)
        n = Notification.objects.get(id=n.id)
        self.assertEqual(n.is_read, False)

    def test_filter_is_read_false(self):
        n = self._makeNotification(is_read=False)
        self._makeNotification(is_read=True)
        self.client.force_authenticate(user=self.follower)
        res = self.client.get(reverse("notification-list") + "?is_read=0")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([d["id"] for d in res.data], [n.id])

    def test_filter_is_read_true(self):
        self._makeNotification(is_read=False)
        n = self._makeNotification(is_read=True)
        self.client.force_authenticate(user=self.follower)
        res = self.client.get(reverse("notification-list") + "?is_read=1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([d["id"] for d in res.data], [n.id])


@patch.object(notification_tasks, "requests")
class RealtimeViewSet(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_updates_subview(self, requests):
        requests.put.return_value.status_code = 200

        u = UserFactory()
        q = QuestionFactory(content="asdf")
        ct = ContentType.objects.get_for_model(q)
        rt = RealtimeRegistration.objects.create(
            creator=u, content_type=ct, object_id=q.id, endpoint="http://example.com/"
        )
        # Some of the above may have created actions, which we don't care about.
        Action.objects.all().delete()
        # This should create an action that will trigger the above.
        a = AnswerFactory(question=q, content="asdf")

        self.client.force_authenticate(user=u)
        url = reverse("realtimeregistration-updates", args=[rt.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        self.assertEqual(len(res.data), 1)
        act = res.data[0]
        self.assertEqual(act["actor"]["username"], a.creator.username)
        self.assertEqual(act["target"]["content"], q.content_parsed)
        self.assertEqual(act["action_object"]["content"], a.content_parsed)

    def test_is_cors(self, requests):
        u = UserFactory()
        q = QuestionFactory()
        self.client.force_authenticate(user=u)
        url = reverse("realtimeregistration-list")
        data = {
            "content_type": "question",
            "object_id": q.id,
            "endpoint": "http://example.com",
        }
        res = self.client.post(url, data, HTTP_ORIGIN="http://example.com")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res["Access-Control-Allow-Origin"], "*")
