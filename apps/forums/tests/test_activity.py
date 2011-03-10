from django.contrib.auth.models import User

from nose.tools import eq_

from activity.models import Action
from forums.models import Forum, Post, Thread
from forums.tests import ForumTestCase


class ReplyLoggingTests(ForumTestCase):
    def setUp(self):
        super(ReplyLoggingTests, self).setUp()
        Action.objects.all().delete()

    def test_activity_logged(self):
        assert not Action.uncached.exists(), 'Actions start empty.'
        orig, replier = User.objects.all()[0:2]
        f = Forum.objects.all()[0]
        t = Thread.objects.create(creator=orig, title='foo', forum=f)
        Post.objects.create(author=orig, content='foo', thread=t)
        assert not Action.uncached.exists(), 'No actions were logged.'

        Post.objects.create(author=replier, content='foo2', thread=t)
        eq_(1, Action.uncached.count(), 'One action was logged.')

        a = Action.uncached.all()[0]
        assert orig in a.users.all(), 'The original poster was notified.'
        assert not replier in a.users.all(), 'The replier was not notified.'
