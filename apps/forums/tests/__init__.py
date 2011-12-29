from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User

from nose.tools import eq_

from forums.models import Forum, Thread, Post, ThreadLockedError
from forums.views import sort_threads
from sumo.tests import (get, LocalizingClient, TestCase, ElasticTestMixin,
                        with_save)
from users.tests import user


class ForumTestCase(TestCase):
    fixtures = ['users.json', 'posts.json', 'forums_permissions.json']
    client_class = LocalizingClient


class ESTestCase(ForumTestCase, ElasticTestMixin):
    def setUp(self):
        super(ESTestCase, self).setUp()
        self.setup_indexes()

    def tearDown(self):
        super(ESTestCase, self).tearDown()
        self.teardown_indexes()


class PostTestCase(ForumTestCase):

    def test_new_post_updates_thread(self):
        """Saving a new post in a thread should update the last_post key in
        that thread to point to the new post."""
        t = Thread.objects.get(pk=2)
        post = t.new_post(author=t.creator, content='an update')
        post.save()
        eq_(post.id, t.last_post_id)

    def test_new_post_updates_forum(self):
        """Saving a new post should update the last_post key in the forum to
        point to the new post."""
        t = Thread.objects.get(pk=2)
        f = t.forum
        post = t.new_post(author=t.creator, content='another update')
        post.save()
        eq_(post.id, f.last_post_id)

    def test_update_post_does_not_update_thread(self):
        """Updating/saving an old post in a thread should _not_ update the
        last_post key in that thread."""
        p = Post.objects.get(pk=2)
        old = p.thread.last_post_id
        p.content = 'updated content'
        p.save()
        eq_(old, p.thread.last_post_id)

    def test_update_forum_does_not_update_thread(self):
        """Updating/saving an old post in a forum should _not_ update the
        last_post key in that forum."""
        p = Post.objects.get(pk=2)
        old = p.thread.forum.last_post_id
        p.content = 'updated content'
        p.save()
        eq_(old, p.thread.forum.last_post_id)

    def test_replies_count(self):
        """The Thread.replies value should remain one less than the number of
        posts in the thread."""
        t = Thread.objects.get(pk=2)
        old = t.replies
        t.new_post(author=t.creator, content='test').save()
        eq_(old + 1, t.replies)

    def test_sticky_threads_first(self):
        """Sticky threads should come before non-sticky threads."""
        thread = Thread.objects.all()[0]
        # Thread 2 is the only sticky thread.
        eq_(2, thread.id)

    def test_thread_sorting(self):
        """After the sticky threads, threads should be sorted by the created
        date of the last post."""
        threads = Thread.objects.filter(is_sticky=False)
        self.assert_(threads[0].last_post.created >
                     threads[1].last_post.created)

    def test_post_sorting(self):
        """Posts should be sorted chronologically."""
        posts = Thread.objects.get(pk=1).post_set.all()
        for i in range(len(posts) - 1):
            self.assert_(posts[i].created <= posts[i + 1].created)

    def test_sorting_creator(self):
        """Sorting threads by creator."""
        threads = sort_threads(Thread.objects, 3, 1)
        self.assert_(threads[0].creator.username >=
                     threads[1].creator.username)

    def test_sorting_replies(self):
        """Sorting threads by replies."""
        threads = sort_threads(Thread.objects, 4)
        self.assert_(threads[0].replies <= threads[1].replies)

    def test_sorting_last_post_desc(self):
        """Sorting threads by last_post descendingly."""
        threads = sort_threads(Thread.objects, 5, 1)
        self.assert_(threads[0].last_post.created >=
                     threads[1].last_post.created)

    def test_thread_last_page(self):
        """Thread's last_page property is accurate."""
        thread = Thread.objects.all()[0]
        # Format: (# replies, # of pages to expect)
        test_data = ((thread.replies, 1),  # Test default
                     (50, 3),  # Test a large number
                     (19, 1),  # Test off-by-one error, low
                     (20, 2),  # Test off-by-one error, high
                    )
        for replies, pages in test_data:
            thread.replies = replies
            eq_(thread.last_page, pages)

    def test_locked_thread(self):
        """Trying to reply to a locked thread should raise an exception."""
        locked = Thread.objects.get(pk=3)
        open = Thread.objects.get(pk=2)
        user1 = User.objects.get(pk=118533)
        fn = lambda: locked.new_post(author=user1, content='empty')
        self.assertRaises(ThreadLockedError, fn)

        # This should not raise an exception.
        open.new_post(author=user1, content='empty')

    def test_post_no_session(self):
        r = get(self.client, 'forums.new_thread',
                kwargs={'forum_slug': 'test-forum'})
        assert(settings.LOGIN_URL in r.redirect_chain[0][0])
        eq_(302, r.redirect_chain[0][1])


class ThreadTestCase(ForumTestCase):

    def test_delete_no_session(self):
        """Delete a thread while logged out redirects."""
        r = get(self.client, 'forums.delete_thread',
                kwargs={'forum_slug': 'test-forum', 'thread_id': 1})
        assert(settings.LOGIN_URL in r.redirect_chain[0][0])
        eq_(302, r.redirect_chain[0][1])


@with_save
def forum(**kwargs):
    if 'name' not in kwargs:
        kwargs['name'] = u'test forum'
    if 'slug' not in kwargs:
        kwargs['slug'] = u'testforum'
    return Forum(**kwargs)


@with_save
def thread(**kwargs):
    defaults = dict(created=datetime.now())
    defaults.update(kwargs)
    if 'creator' not in kwargs and 'creator_id' not in kwargs:
        defaults['creator'] = user(save=True)
    if 'forum' not in kwargs and 'forum_id' not in kwargs:
        defaults['forum'] = forum(save=True)
    return Thread(**defaults)


@with_save
def post(**kwargs):
    defaults = dict()
    defaults.update(kwargs)
    if 'author' not in kwargs and 'author_id' not in kwargs:
        defaults['author'] = user(save=True)
    return Post(**defaults)
