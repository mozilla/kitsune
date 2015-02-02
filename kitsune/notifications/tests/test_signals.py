from nose.tools import eq_

from actstream.actions import follow
from actstream.signals import action
from actstream.models import Action

from kitsune.notifications.models import Notification
from kitsune.questions.tests import answer, question
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import profile


class TestNotificationsSentFromActions(TestCase):

    def test_following_actor(self):
        follower = profile().user
        followed = profile().user
        q = question(creator=followed, save=True)
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
        follow(follower, q, actor_only=False)

        # Make a new action for the above. This should trigger notifications.
        action.send(q.creator, verb='edited', action_object=q)
        act = Action.objects.order_by('-id')[0]
        notification = Notification.objects.get(action=act)

        eq_(notification.owner, follower)
        eq_(notification.action, act)
