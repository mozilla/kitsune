from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from kitsune.access.tests import PermissionFactory
from kitsune.flagit.models import FlaggedObject
from kitsune.forums import POSTS_PER_PAGE
from kitsune.forums.events import NewPostEvent, NewThreadEvent
from kitsune.forums.models import Forum, Thread, Post
from kitsune.forums.tests import ForumTestCase, ForumFactory, ThreadFactory, PostFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory


YESTERDAY = datetime.now() - timedelta(days=1)


class ForumModelTestCase(ForumTestCase):
    def test_forum_absolute_url(self):
        f = ForumFactory()

        eq_('/forums/%s' % f.slug,
            f.get_absolute_url())

    def test_thread_absolute_url(self):
        t = ThreadFactory()

        eq_('/forums/%s/%s' % (t.forum.slug, t.id),
            t.get_absolute_url())

    def test_post_absolute_url(self):
        t = ThreadFactory(posts=[])

        # Fill out the first page with posts from yesterday.
        p1 = PostFactory(thread=t, created=YESTERDAY)
        PostFactory.create_batch(POSTS_PER_PAGE - 1, created=YESTERDAY, thread=t)
        # Second page post from today.
        p2 = PostFactory(thread=t)

        url = reverse('forums.posts',
                      kwargs={'forum_slug': p1.thread.forum.slug,
                              'thread_id': p1.thread.id})
        eq_(urlparams(url, hash='post-%s' % p1.id), p1.get_absolute_url())

        url = reverse('forums.posts',
                      kwargs={'forum_slug': p2.thread.forum.slug,
                              'thread_id': p2.thread.id})
        exp_ = urlparams(url, hash='post-%s' % p2.id, page=2)
        eq_(exp_, p2.get_absolute_url())

    def test_post_page(self):
        t = ThreadFactory()
        # Fill out the first page with posts from yesterday.
        page1 = PostFactory.create_batch(POSTS_PER_PAGE, thread=t, created=YESTERDAY)
        # Second page post from today.
        p2 = PostFactory(thread=t)

        for p in page1:
            eq_(1, p.page)
        eq_(2, p2.page)

    def test_delete_post_removes_flag(self):
        """Deleting a post also removes the flags on that post."""
        p = PostFactory()

        u = UserFactory()
        FlaggedObject.objects.create(
            status=0, content_object=p, reason='language', creator_id=u.id)
        eq_(1, FlaggedObject.objects.count())

        p.delete()
        eq_(0, FlaggedObject.objects.count())

    def test_thread_last_post_url(self):
        t = ThreadFactory()
        lp = t.last_post
        f = t.forum
        url = t.get_last_post_url()
        assert f.slug in url
        assert str(t.id) in url
        assert '#post-%s' % lp.id in url
        assert 'last=%s' % lp.id in url

    def test_last_post_updated(self):
        # Adding/Deleting the last post in a thread and forum should
        # update the last_post field
        orig_post = PostFactory(created=YESTERDAY)
        t = orig_post.thread

        # add a new post, then check that last_post is updated
        new_post = PostFactory(thread=t, content='test')
        f = Forum.objects.get(id=t.forum_id)
        t = Thread.objects.get(id=t.id)
        eq_(f.last_post.id, new_post.id)
        eq_(t.last_post.id, new_post.id)

        # delete the new post, then check that last_post is updated
        new_post.delete()
        f = Forum.objects.get(id=f.id)
        t = Thread.objects.get(id=t.id)
        eq_(f.last_post.id, orig_post.id)
        eq_(t.last_post.id, orig_post.id)

    def test_public_access(self):
        # Assert Forums think they're publicly viewable and postable
        # at appropriate times.

        # By default, users have access to forums that aren't restricted.
        u = UserFactory()
        f = ForumFactory()
        assert f.allows_viewing_by(u)
        assert f.allows_posting_by(u)

    def test_access_restriction(self):
        """Assert Forums are inaccessible to the public when restricted."""
        # If the a forum has 'forums_forum.view_in_forum' permission defined,
        # then it isn't public by default. If it has
        # 'forums_forum.post_in_forum', then it isn't postable to by default.
        f = ForumFactory()
        ct = ContentType.objects.get_for_model(f)
        PermissionFactory(codename='forums_forum.view_in_forum', content_type=ct, object_id=f.id)
        PermissionFactory(codename='forums_forum.post_in_forum', content_type=ct, object_id=f.id)

        unprivileged_user = UserFactory()
        assert not f.allows_viewing_by(unprivileged_user)
        assert not f.allows_posting_by(unprivileged_user)

    def test_move_updates_last_posts(self):
        # Moving the thread containing a forum's last post to a new
        # forum should update the last_post of both
        # forums. Consequently, deleting the last post shouldn't
        # delete the old forum. [bug 588994]

        # Setup forum to move latest thread from.
        old_forum = ForumFactory()
        t1 = ThreadFactory(forum=old_forum, posts=[])
        p1 = PostFactory(thread=t1, created=YESTERDAY)
        t2 = ThreadFactory(forum=old_forum, posts=[])
        p2 = PostFactory(thread=t2)  # Newest post of all.

        # Setup forum to move latest thread to.
        new_forum = ForumFactory()
        t3 = ThreadFactory(forum=new_forum, posts=[])
        p3 = PostFactory(thread=t3, created=YESTERDAY)

        # Verify the last_post's are correct.
        eq_(p2, Forum.objects.get(id=old_forum.id).last_post)
        eq_(p3, Forum.objects.get(id=new_forum.id).last_post)

        # Move the t2 thread.
        t2 = Thread.objects.get(id=t2.id)
        t2.forum = new_forum
        t2.save()

        # Old forum's last_post updated?
        eq_(p1.id, Forum.objects.get(id=old_forum.id).last_post_id)

        # New forum's last_post updated?
        eq_(p2.id, Forum.objects.get(id=new_forum.id).last_post_id)

        # Delete the post, and both forums should still exist:
        p2.delete()
        eq_(1, Forum.objects.filter(id=old_forum.id).count())
        eq_(1, Forum.objects.filter(id=new_forum.id).count())

    def test_delete_removes_watches(self):
        f = ForumFactory()
        NewThreadEvent.notify('me@me.com', f)
        assert NewThreadEvent.is_notifying('me@me.com', f)
        f.delete()
        assert not NewThreadEvent.is_notifying('me@me.com', f)

    def test_last_post_creator_deleted(self):
        """Delete the creator of the last post and verify forum survives."""
        # Create a post and verify it is the last one in the forum.
        post = PostFactory(content='test')
        forum = post.thread.forum
        eq_(forum.last_post.id, post.id)

        # Delete the post creator, then check the forum still exists
        post.author.delete()
        forum = Forum.objects.get(id=forum.id)
        eq_(forum.last_post, None)


class ThreadModelTestCase(ForumTestCase):
    def test_delete_thread_with_last_forum_post(self):
        # Deleting the thread with a forum's last post should update
        # the last_post field on the forum
        t = ThreadFactory()
        f = t.forum
        last_post = f.last_post

        # add a new thread and post, verify last_post updated
        t = ThreadFactory(title='test', forum=f, posts=[])
        p = PostFactory(thread=t, content='test', author=t.creator)
        f = Forum.objects.get(id=f.id)
        eq_(f.last_post.id, p.id)

        # delete the post, verify last_post updated
        t.delete()
        f = Forum.objects.get(id=f.id)
        eq_(f.last_post.id, last_post.id)
        eq_(Thread.objects.filter(pk=t.id).count(), 0)

    def test_delete_removes_watches(self):
        t = ThreadFactory()
        NewPostEvent.notify('me@me.com', t)
        assert NewPostEvent.is_notifying('me@me.com', t)
        t.delete()
        assert not NewPostEvent.is_notifying('me@me.com', t)

    def test_delete_last_and_only_post_in_thread(self):
        """Deleting the only post in a thread should delete the thread"""
        t = ThreadFactory()
        eq_(1, t.post_set.count())
        t.delete()
        eq_(0, Thread.objects.filter(pk=t.id).count())


class SaveDateTestCase(ForumTestCase):
    """
    Test that Thread and Post save methods correctly handle created
    and updated dates.
    """

    delta = timedelta(milliseconds=3000)

    def setUp(self):
        super(SaveDateTestCase, self).setUp()

        self.user = UserFactory()
        self.thread = ThreadFactory()
        self.forum = self.thread.forum

    def assertDateTimeAlmostEqual(self, a, b, delta, msg=None):
        """Assert that two datetime objects are within `range` (a timedelta).
        """
        diff = abs(a - b)
        assert diff < abs(delta), msg or '%s ~= %s' % (a, b)

    def test_save_thread_no_created(self):
        """Saving a new thread should behave as if auto_add_now was set."""
        t = ThreadFactory(forum=self.forum, title='foo', creator=self.user)
        now = datetime.now()
        self.assertDateTimeAlmostEqual(now, t.created, self.delta)

    def test_save_thread_created(self):
        # Saving a new thread that already has a created date should
        # respect that created date.
        created = datetime(1992, 1, 12, 9, 48, 23)
        t = Thread(forum=self.forum, title='foo', creator=self.user, created=created)
        eq_(created, t.created)

    def test_save_old_thread_created(self):
        """Saving an old thread should not change its created date."""
        t = ThreadFactory(created=YESTERDAY)
        t = Thread.objects.get(id=t.id)
        created = t.created

        # Now make an update to the thread and resave. Created shouldn't change.
        t.title = 'new title'
        t.save()
        t = Thread.objects.get(id=t.id)
        eq_(created, t.created)

    def test_save_new_post_no_timestamps(self):
        # Saving a new post should behave as if auto_add_now was set on
        # created and auto_now set on updated.
        p = PostFactory(thread=self.thread, content='bar', author=self.user)
        now = datetime.now()
        self.assertDateTimeAlmostEqual(now, p.created, self.delta)
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

    def test_save_old_post_no_timestamps(self):
        """Saving an existing post should update the updated date."""
        created = datetime(2010, 5, 4, 14, 4, 22)
        updated = datetime(2010, 5, 4, 14, 4, 31)
        p = PostFactory(thread=self.thread, created=created, updated=updated)

        eq_(updated, p.updated)

        p.content = 'baz'
        p.updated_by = self.user
        p.save()
        now = datetime.now()

        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)
        eq_(created, p.created)

    def test_save_new_post_timestamps(self):
        # Saving a new post should allow you to override auto_add_now-
        # and auto_now-like functionality.
        created_ = datetime(1992, 1, 12, 10, 12, 32)
        p = Post(thread=self.thread, content='bar', author=self.user,
                 created=created_, updated=created_)
        p.save()
        eq_(created_, p.created)
        eq_(created_, p.updated)

    def test_content_parsed_sanity(self):
        """The content_parsed field is populated."""
        p = PostFactory(thread=self.thread, content='yet another post')
        eq_('<p>yet another post\n</p>', p.content_parsed)
