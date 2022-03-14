from unittest import mock

from actstream.actions import follow
from actstream.models import Action, Follow
from actstream.signals import action
from django.contrib.contenttypes.models import ContentType

from kitsune.notifications import tasks as notification_tasks
from kitsune.notifications.models import (
    Notification,
    PushNotificationRegistration,
    RealtimeRegistration,
)
from kitsune.notifications.tests import NotificationFactory
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class TestNotificationsSentFromActions(TestCase):
    def test_following_actor(self):
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

        self.assertEqual(notification.owner, follower)
        self.assertEqual(notification.action, act)

    def test_following_target(self):
        follower = UserFactory()
        q = QuestionFactory()
        ans = AnswerFactory(question=q)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, q, actor_only=False)

        # Make a new action for the above. This should trigger notifications.
        action.send(ans.creator, verb="answered", action_object=ans, target=q)
        act = Action.objects.order_by("-id")[0]
        notification = Notification.objects.get(action=act)

        self.assertEqual(notification.owner, follower)
        self.assertEqual(notification.action, act)

    def test_following_action_object(self):
        follower = UserFactory()
        q = QuestionFactory()
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, q, actor_only=False)

        # Make a new action for the above. This should trigger notifications.
        action.send(q.creator, verb="edited", action_object=q)
        act = Action.objects.order_by("-id")[0]
        notification = Notification.objects.get(action=act)

        self.assertEqual(notification.owner, follower)
        self.assertEqual(notification.action, act)

    def test_no_action_for_self(self):
        """Test that a notification is not sent for actions the user took."""
        follower = UserFactory()
        q = QuestionFactory(creator=follower)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, q, actor_only=False)

        # Make a new action for the above. This should not trigger notifications.
        action.send(q.creator, verb="edited", action_object=q)
        act = Action.objects.order_by("-id")[0]
        self.assertEqual(Notification.objects.filter(action=act).count(), 0)


@mock.patch.object(notification_tasks, "requests")
class TestSimplePushNotifier(TestCase):
    def test_simple_push_send(self, requests):
        """Verify that SimplePush registrations are called."""
        response = mock.Mock()
        response.status_code = 200
        requests.put.return_value = response

        u = UserFactory()
        url = "http://example.com/simple_push/asdf"
        PushNotificationRegistration.objects.create(creator=u, push_url=url)
        n = NotificationFactory(owner=u)
        requests.put.assert_called_once_with(url, "version={}".format(n.id))

    def test_simple_push_not_sent(self, requests):
        """Verify that no request is made when there is no SimplePush registration."""
        NotificationFactory()
        requests.put.assert_not_called()

    def test_simple_push_retry(self, requests):
        response = mock.MagicMock()
        response.status_code = 503
        response.json.return_value = {"errno": 202}
        requests.put.return_value = response

        u = UserFactory()
        url = "http://example.com/simple_push/asdf"
        PushNotificationRegistration.objects.create(creator=u, push_url=url)
        n = NotificationFactory(owner=u)

        # The push notification handler should try, and then retry 3 times before giving up.
        self.assertEqual(
            requests.put.call_args_list,
            [
                ((url, "version={}".format(n.id)), {}),
                ((url, "version={}".format(n.id)), {}),
                ((url, "version={}".format(n.id)), {}),
                ((url, "version={}".format(n.id)), {}),
            ],
        )

    def test_from_action_to_simple_push(self, requests):
        """Test that when an action is created, it results in a push notification being sent."""
        response = mock.Mock()
        response.status_code = 200
        requests.put.return_value = response

        # Create a user.
        u = UserFactory()
        # Register them to receive push notifications.
        url = "http://example.com/simple_push/asdf"
        PushNotificationRegistration.objects.create(creator=u, push_url=url)
        # Make them follow an object.
        q = QuestionFactory()
        follow(u, q, actor_only=False)
        # Create an action involving that object
        action.send(UserFactory(), verb="looked at funny", action_object=q)
        n = Notification.objects.get(owner=u)
        # Assert that they got notified.
        requests.put.assert_called_once_with(url, "version={}".format(n.id))

    def test_from_action_to_realtime_notification(self, requests):
        """
        Test that when an action is created, it results in a realtime notification being sent.
        """
        response = mock.Mock()
        response.status_code = 200
        requests.put.return_value = response

        # Create a user
        u = UserFactory()
        # Register realtime notifications for that user on a question
        q = QuestionFactory()
        url = "http://example.com/simple_push/asdf"
        ct = ContentType.objects.get_for_model(q)
        RealtimeRegistration.objects.create(
            creator=u, endpoint=url, content_type=ct, object_id=q.id
        )
        # Create an action involving that question
        action.send(UserFactory(), verb="looked at funny", action_object=q)
        a = Action.objects.order_by("-id")[0]
        # Assert that they got notified.
        requests.put.assert_called_once_with(url, "version={}".format(a.id))
