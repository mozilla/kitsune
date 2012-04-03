from nose.tools import eq_

from activity.models import Action
from forums.tests import ForumTestCase, thread, post
from users.tests import user


class ReplyLoggingTests(ForumTestCase):
    def setUp(self):
        super(ReplyLoggingTests, self).setUp()
        Action.objects.all().delete()

    def test_activity_logged(self):
        assert not Action.uncached.exists(), 'Actions start empty.'
        orig = user(save=True)
        replier = user(save=True)
        t = thread(creator=orig, title='foo', save=True)
        post(author=orig, content='foo', thread=t, save=True)
        assert not Action.uncached.exists(), 'No actions were logged.'

        post(author=replier, content='foo2', thread=t, save=True)
        eq_(1, Action.uncached.count(), 'One action was logged.')

        a = Action.uncached.all()[0]
        assert orig in a.users.all(), 'The original poster was notified.'
        assert not replier in a.users.all(), 'The replier was not notified.'
