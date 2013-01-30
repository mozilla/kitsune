from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from access.tests import permission
from forums import POSTS_PER_PAGE
from forums.events import NewPostEvent, NewThreadEvent
from forums.models import Forum, Thread, Post
from forums.tests import ForumTestCase, forum, thread, post
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from users.tests import user


YESTERDAY = datetime.now() - timedelta(days=1)


class ForumModelTestCase(ForumTestCase):
    def test_forum_absolute_url(self):
        f = forum(save=True)

        eq_('/forums/%s' % f.slug,
            f.get_absolute_url())

    def test_thread_absolute_url(self):
        t = thread(save=True)

        eq_('/forums/%s/%s' % (t.forum.slug, t.id),
            t.get_absolute_url())

    def test_post_absolute_url(self):
        t = thread(save=True)

        # Fill out the first page with posts from yesterday.
        p1 = post(thread=t, created=YESTERDAY, save=True)
        for i in range(POSTS_PER_PAGE - 1):
            post(thread=t, created=YESTERDAY, save=True)
        # Second page post from today.
        p2 = post(thread=t, save=True)

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
        t = thread(save=True)
        # Fill out the first page with posts from yesterday.
        page1 = []
        for i in range(POSTS_PER_PAGE):
            page1.append(post(thread=t, created=YESTERDAY, save=True))
        # Second page post from today.
        p2 = post(thread=t, save=True)

        for p in page1:
            eq_(1, p.page)
        eq_(2, p2.page)

    def test_thread_last_post_url(self):
        t = thread(save=True)
        post(thread=t, save=True)
        lp = t.last_post
        f = t.forum
        url = t.get_last_post_url()
        assert f.slug in url
        assert str(t.id) in url
        assert '#post-%s' % lp.id in url
        assert 'last=%s' % lp.id in url

    def test_last_post_updated(self):
        """Adding/Deleting the last post in a thread and forum should
        update the last_post field
        """
        orig_post = post(created=YESTERDAY, save=True)
        t = orig_post.thread

        # add a new post, then check that last_post is updated
        new_post = post(thread=t, content="test", save=True)
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
        """Assert Forums think they're publicly viewable and postable at
        appropriate times."""
        # By default, users have access to forums that aren't restricted.
        u = user(save=True)
        f = forum(save=True)
        assert f.allows_viewing_by(u)
        assert f.allows_posting_by(u)

    def test_access_restriction(self):
        """Assert Forums are inaccessible to the public when restricted."""
        # If the a forum has 'forums_forum.view_in_forum' permission defined,
        # then it isn't public by default. If it has
        # 'forums_forum.post_in_forum', then it isn't postable to by default.
        f = forum(save=True)
        ct = ContentType.objects.get_for_model(f)
        permission(codename='forums_forum.view_in_forum', content_type=ct,
                   object_id=f.id, save=True)
        permission(codename='forums_forum.post_in_forum', content_type=ct,
                   object_id=f.id, save=True)

        unprivileged_user = user(save=True)
        assert not f.allows_viewing_by(unprivileged_user)
        assert not f.allows_posting_by(unprivileged_user)

    def test_move_updates_last_posts(self):
        """Moving the thread containing a forum's last post to a new forum
        should update the last_post of both forums. Consequently, deleting
        the last post shouldn't delete the old forum. [bug 588994]"""
        # Setup forum to move latest thread from.
        old_forum = forum(save=True)
        t1 = thread(forum=old_forum, save=True)
        p1 = post(thread=t1, created=YESTERDAY, save=True)
        t2 = thread(forum=old_forum, save=True)
        p2 = post(thread=t2, save=True)  # Newest post of all.

        # Setup forum to move latest thread to.
        new_forum = forum(save=True)
        t3 = thread(forum=new_forum, save=True)
        p3 = post(thread=t3, created=YESTERDAY, save=True)

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
        f = forum(save=True)
        NewThreadEvent.notify('me@me.com', f)
        assert NewThreadEvent.is_notifying('me@me.com', f)
        f.delete()
        assert not NewThreadEvent.is_notifying('me@me.com', f)

    def test_last_post_creator_deleted(self):
        """Delete the creator of the last post and verify forum survives."""
        # Create a post and verify it is the last one in the forum.
        post_ = post(content="test", save=True)
        forum_ = post_.thread.forum
        eq_(forum_.last_post.id, post_.id)

        # Delete the post creator, then check the forum still exists
        post_.author.delete()
        forum_ = Forum.objects.get(id=forum_.id)
        eq_(forum_.last_post, None)


class ThreadModelTestCase(ForumTestCase):
    def test_delete_thread_with_last_forum_post(self):
        """Deleting the thread with a forum's last post should
        update the last_post field on the forum
        """
        t = thread(save=True)
        post(thread=t, save=True)
        f = t.forum
        last_post = f.last_post

        # add a new thread and post, verify last_post updated
        t = thread(title="test", forum=f, save=True)
        p = post(thread=t, content="test", author=t.creator, save=True)
        f = Forum.objects.get(id=f.id)
        eq_(f.last_post.id, p.id)

        # delete the post, verify last_post updated
        t.delete()
        f = Forum.objects.get(id=f.id)
        eq_(f.last_post.id, last_post.id)
        eq_(Thread.objects.filter(pk=t.id).count(), 0)

    def test_delete_removes_watches(self):
        t = thread(save=True)
        NewPostEvent.notify('me@me.com', t)
        assert NewPostEvent.is_notifying('me@me.com', t)
        t.delete()
        assert not NewPostEvent.is_notifying('me@me.com', t)

    def test_delete_last_and_only_post_in_thread(self):
        """Deleting the only post in a thread should delete the thread"""
        t = thread(save=True)
        post(thread=t, save=True)

        eq_(1, t.post_set.count())
        t.delete()
        eq_(0, Thread.uncached.filter(pk=t.id).count())


class SaveDateTestCase(ForumTestCase):
    """
    Test that Thread and Post save methods correctly handle created
    and updated dates.
    """

    delta = timedelta(milliseconds=300)

    def setUp(self):
        super(SaveDateTestCase, self).setUp()

        self.user = user(save=True)
        self.thread = thread(save=True)
        self.forum = self.thread.forum

    def assertDateTimeAlmostEqual(self, a, b, delta, msg=None):
        """
        Assert that two datetime objects are within `range` (a timedelta).
        """
        diff = abs(a - b)
        assert diff < abs(delta), msg or '%s ~= %s' % (a, b)

    def test_save_thread_no_created(self):
        """Saving a new thread should behave as if auto_add_now was set."""
        t = thread(forum=self.forum, title='foo', creator=self.user,
                   save=True)
        t.save()
        now = datetime.now()
        self.assertDateTimeAlmostEqual(now, t.created, self.delta)

    def test_save_thread_created(self):
        """
        Saving a new thread that already has a created date should respect
        that created date.
        """
        created = datetime(1992, 1, 12, 9, 48, 23)
        t = thread(forum=self.forum, title='foo', creator=self.user,
                   created=created, save=True)
        t.save()
        eq_(created, t.created)

    def test_save_old_thread_created(self):
        """Saving an old thread should not change its created date."""
        t = thread(created=YESTERDAY, save=True)
        t = Thread.objects.get(id=t.id)
        created = t.created

        # Now make an update to the thread and resave. Created shouldn't
        # change.
        t.title = 'new title'
        t.save()
        t = Thread.objects.get(id=t.id)
        eq_(created, t.created)

    def test_save_new_post_no_timestamps(self):
        """
        Saving a new post should behave as if auto_add_now was set on
        created and auto_now set on updated.
        """
        p = post(thread=self.thread, content='bar', author=self.user,
                 save=True)
        now = datetime.now()
        self.assertDateTimeAlmostEqual(now, p.created, self.delta)
        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)

    def test_save_old_post_no_timestamps(self):
        """
        Saving an existing post should update the updated date.
        """
        created = datetime(2010, 5, 4, 14, 4, 22)
        updated = datetime(2010, 5, 4, 14, 4, 31)
        p = post(thread=self.thread, created=created, updated=updated,
                 save=True)

        eq_(updated, p.updated)

        p.content = 'baz'
        p.updated_by = self.user
        p.save()
        now = datetime.now()

        self.assertDateTimeAlmostEqual(now, p.updated, self.delta)
        eq_(created, p.created)

    def test_save_new_post_timestamps(self):
        """
        Saving a new post should allow you to override auto_add_now- and
        auto_now-like functionality.
        """
        created_ = datetime(1992, 1, 12, 10, 12, 32)
        p = Post(thread=self.thread, content='bar', author=self.user,
                 created=created_, updated=created_)
        p.save()
        eq_(created_, p.created)
        eq_(created_, p.updated)

    def test_content_parsed_sanity(self):
        """The content_parsed field is populated."""
        p = post(thread=self.thread, content='yet another post', save=True)
        eq_('<p>yet another post\n</p>', p.content_parsed)
