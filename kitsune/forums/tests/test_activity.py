from nose.tools import eq_

from kitsune.activity.models import Action
from kitsune.forums.tests import ForumTestCase, thread, post as forum_post
from kitsune.sumo.tests import post
from kitsune.users.tests import user


class ReplyLoggingTests(ForumTestCase):
    def setUp(self):
        super(ReplyLoggingTests, self).setUp()
        Action.objects.all().delete()

    def test_activity_logged(self):
        assert not Action.uncached.exists(), 'Actions start empty.'
        orig = user(save=True)
        replier = user(save=True)
        t = thread(creator=orig, title='foo', save=True)
        forum_post(author=orig, content='foo', thread=t, save=True)
        assert not Action.uncached.exists(), 'No actions were logged.'

        self.client.login(username=replier.username, password='testpass')
        post(self.client, 'forums.reply', {'content': 'foo bar'},
             args=[t.forum.slug, t.id])
        eq_(1, Action.uncached.count(), 'One action was logged.')

        a = Action.uncached.all()[0]
        assert orig in a.users.all(), 'The original poster was notified.'
        assert not replier in a.users.all(), 'The replier was not notified.'
