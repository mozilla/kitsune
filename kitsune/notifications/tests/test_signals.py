from actstream.actions import follow
from actstream.signals import action
from actstream.models import Action, Follow
from mock import patch
from nose.tools import eq_

from kitsune.notifications import models as notification_models
from kitsune.notifications.models import Notification, PushNotificationRegistration
from kitsune.notifications.tests import notification
from kitsune.questions.tests import answer, question
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import profile


class TestNotificationsSentFromActions(TestCase):

    def test_following_actor(self):
        follower = profile().user
        followed = profile().user
        q = question(creator=followed, save=True)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, followed)

        # Make a new action for the above. This should trigger notifications
        action.send(followed, verb='asked', action_object=q)
        act = Action.objects.order_by('-id')[0]
        notification = Notification.objects.get(action=act)

        eq_(notification.owner, follower)
        eq_(notification.action, act)

    def test_following_target(self):
        follower = profile().user
        q = question(save=True)
        ans = answer(question=q, save=True)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, q, actor_only=False)

        # Make a new action for the above. This should trigger notifications.
        action.send(ans.creator, verb='answered', action_object=ans, target=q)
        act = Action.objects.order_by('-id')[0]
        notification = Notification.objects.get(action=act)

        eq_(notification.owner, follower)
        eq_(notification.action, act)

    def test_following_action_object(self):
        follower = profile().user
        q = question(save=True)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, q, actor_only=False)

        # Make a new action for the above. This should trigger notifications.
        action.send(q.creator, verb='edited', action_object=q)
        act = Action.objects.order_by('-id')[0]
        notification = Notification.objects.get(action=act)

        eq_(notification.owner, follower)
        eq_(notification.action, act)

    def test_no_action_for_self(self):
        """Test that a notification is not sent for actions the user took."""
        follower = profile().user
        q = question(creator=follower, save=True)
        # The above might make follows, which this test isn't about. Clear them out.
        Follow.objects.all().delete()
        follow(follower, q, actor_only=False)

        # Make a new action for the above. This should not trigger notifications.
        action.send(q.creator, verb='edited', action_object=q)
        act = Action.objects.order_by('-id')[0]
        eq_(Notification.objects.filter(action=act).count(), 0)


@patch.object(notification_models, 'requests')
class TestSimplePushNotifier(TestCase):

    def test_simple_push_send(self, requests):
        """Verify that SimplePush registrations are called."""
        u = profile().user
        url = 'http://example.com/simple_push/asdf'
        PushNotificationRegistration.objects.create(creator=u, push_url=url)
        n = notification(owner=u, save=True)
        requests.put.assert_called_once_with(url, 'version={}'.format(n.id))

    def test_simple_push_not_sent(self, requests):
        """Verify that no request is made when there is no SimplePush registration."""
        notification(save=True)
        requests.put.assert_not_called()
