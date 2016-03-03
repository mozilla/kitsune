import datetime

from nose.tools import eq_

from kitsune.kbforums.models import Thread
from kitsune.kbforums.tests import KBForumTestCase, ThreadFactory, PostFactory
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import DocumentFactory


class KBForumModelTestCase(KBForumTestCase):

    def test_thread_absolute_url(self):
        t = ThreadFactory()
        exp_ = reverse('wiki.discuss.posts', locale=t.document.locale,
                       args=[t.document.slug, t.id])
        eq_(exp_, t.get_absolute_url())

    def test_post_absolute_url(self):
        t = ThreadFactory()
        p = t.new_post(creator=t.creator, content='foo')
        url_ = reverse('wiki.discuss.posts',
                       locale=p.thread.document.locale,
                       args=[p.thread.document.slug, p.thread.id])
        exp_ = urlparams(url_, hash='post-%s' % p.id)
        eq_(exp_, p.get_absolute_url())

    def test_last_post_updated(self):
        """Adding/Deleting the last post in a thread should
        update the last_post field
        """
        t = ThreadFactory()
        u = UserFactory()

        # add a new post, then check that last_post is updated
        new_post = t.new_post(creator=u, content="test")
        eq_(t.last_post.id, new_post.id)

        # delete the new post, then check that last_post is updated
        new_post.delete()
        self.assertIsNone(t.last_post.id)


class KBThreadModelTestCase(KBForumTestCase):

    def test_delete_last_and_only_post_in_thread(self):
        """Deleting the only post in a thread should delete the thread"""
        t = ThreadFactory(title="test")
        p = t.new_post(creator=t.creator, content="test")
        eq_(1, t.post_set.count())
        p.delete()
        eq_(0, Thread.objects.filter(pk=t.id).count())


class KBSaveDateTestCase(KBForumTestCase):
    """
    Test that Thread and Post save methods correctly handle created
    and updated dates.
    """

    delta = datetime.timedelta(milliseconds=3000)

    def setUp(self):
        super(KBSaveDateTestCase, self).setUp()

        self.user = UserFactory()
        self.doc = DocumentFactory()
        self.thread = ThreadFactory(created=datetime.datetime(2010, 1, 12, 9, 48, 23))

    def assertDateTimeAlmostEqual(self, a, b, delta, msg=None):
        """
        Assert that two datetime objects are within `range` (a timedelta).
        """
        diff = abs(a - b)
        assert diff < abs(delta), msg or '%s ~= %s' % (a, b)

    def test_save_thread_no_created(self):
        """Saving a new thread should behave as if auto_add_now was set."""
        t = self.doc.thread_set.create(title='foo', creator=self.user)
        t.save()
        now = datetime.datetime.now()
        self.assertDateTimeAlmostEqual(now, t.created, self.delta)

    def test_save_thread_created(self):
        """
        Saving a new thread that already has a created date should respect
        that created date.
        """
        created = datetime.datetime(1992, 1, 12, 9, 48, 23)
        t = self.doc.thread_set.create(title='foo', creator=self.user,
                                       created=created)
        t.save()
        eq_(created, t.created)

    def test_save_old_thread_created(self):
        """Saving an old thread should not change its created date."""
        t = ThreadFactory()
        created = t.created
        t.save()
        eq_(created, t.created)

    def test_save_new_post_no_timestamps(self):
        """
        Saving a new post should behave as if auto_add_now was set on
        created and auto_now set on updated.
        """
        p = self.thread.new_post(creator=self.user, content='bar')
        now = datetime.datetime.now()
        self.assertDateTimeAlmostEqual(now, p.created, self.delta)
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

    def test_save_old_post_no_timestamps(self):
        """
        Saving an existing post should update the updated date.
        """
        now = datetime.datetime.now()

        p = self.thread.new_post(creator=self.user, content='bar')
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

        p.content = 'baz'
        p.updated_by = self.user
        p.save()

        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

    def test_save_new_post_timestamps(self):
        """
        Saving a new post should not allow you to override auto_add_now- and
        auto_now-like functionality.
        """
        created_ = datetime.datetime(1992, 1, 12, 10, 12, 32)
        p = PostFactory(thread=self.thread, creator=self.user, created=created_, updated=created_)

        now = datetime.datetime.now()
        self.assertDateTimeAlmostEqual(now, p.created, self.delta)
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

    def test_content_parsed_sanity(self):
        """The content_parsed field is populated."""
        p = PostFactory(content='yet another post')
        eq_('<p>yet another post\n</p>', p.content_parsed)
