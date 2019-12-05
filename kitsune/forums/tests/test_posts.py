from datetime import datetime, timedelta

from django.conf import settings

from nose.tools import eq_, raises

from kitsune.forums.models import Thread, Forum, ThreadLockedError
from kitsune.forums.tests import ForumTestCase, ThreadFactory, PostFactory
from kitsune.forums.views import sort_threads
from kitsune.sumo.tests import get
from kitsune.users.tests import UserFactory


class PostTestCase(ForumTestCase):

    def test_new_post_updates_thread(self):
        # Saving a new post in a thread should update the last_post
        # key in that thread to point to the new post.
        t = ThreadFactory()
        PostFactory(thread=t)
        p = t.new_post(author=t.creator, content='an update')
        p.save()
        t = Thread.objects.get(id=t.id)
        eq_(p.id, t.last_post_id)

    def test_new_post_updates_forum(self):
        # Saving a new post should update the last_post key in the
        # forum to point to the new post.
        t = ThreadFactory()
        PostFactory(thread=t)
        p = t.new_post(author=t.creator, content='another update')
        p.save()
        f = Forum.objects.get(id=t.forum_id)
        eq_(p.id, f.last_post_id)

    def test_update_post_does_not_update_thread(self):
        # Updating/saving an old post in a thread should _not_ update
        # the last_post key in that thread.
        t = ThreadFactory()
        old = PostFactory(thread=t)
        last = PostFactory(thread=t)
        old.content = 'updated content'
        old.save()
        eq_(last.id, old.thread.last_post_id)

    def test_update_forum_does_not_update_thread(self):
        # Updating/saving an old post in a forum should _not_ update
        # the last_post key in that forum.
        t = ThreadFactory()
        old = PostFactory(thread=t)
        last = PostFactory(thread=t)
        old.content = 'updated content'
        old.save()
        eq_(last.id, t.forum.last_post_id)

    def test_replies_count(self):
        # The Thread.replies value should remain one less than the
        # number of posts in the thread.
        t = ThreadFactory(posts=[{}, {}, {}])
        old = t.replies
        eq_(2, old)
        t.new_post(author=t.creator, content='test').save()
        eq_(old + 1, t.replies)

    def test_sticky_threads_first(self):
        # Sticky threads should come before non-sticky threads.
        t = ThreadFactory()
        yesterday = datetime.now() - timedelta(days=1)
        sticky = ThreadFactory(forum=t.forum, is_sticky=True, posts=[{'created': yesterday}])

        # The older sticky thread shows up first.
        eq_(sticky.id, Thread.objects.all()[0].id)

    def test_thread_sorting(self):
        # After the sticky threads, threads should be sorted by the
        # created date of the last post.

        # Make sure the datetimes are different.
        PostFactory(created=datetime.now() - timedelta(days=1))
        PostFactory()
        Thread(is_sticky=True)

        threads = Thread.objects.filter(is_sticky=False)
        self.assertTrue(threads[0].last_post.created >
                     threads[1].last_post.created)

    def test_post_sorting(self):
        """Posts should be sorted chronologically."""
        now = datetime.now()
        t = ThreadFactory(posts=[{'created': now - timedelta(days=n)} for n in [0, 1, 4, 7, 11]])
        posts = t.post_set.all()
        for i in range(len(posts) - 1):
            self.assertTrue(posts[i].created <= posts[i + 1].created)

    def test_sorting_creator(self):
        """Sorting threads by creator."""
        ThreadFactory(creator__username='aaa')
        ThreadFactory(creator__username='bbb')
        threads = sort_threads(Thread.objects, 3, 1)
        self.assertTrue(threads[0].creator.username >= threads[1].creator.username)

    def test_sorting_replies(self):
        """Sorting threads by replies."""
        ThreadFactory(posts=[{}, {}, {}])
        ThreadFactory()
        threads = sort_threads(Thread.objects, 4)
        self.assertTrue(threads[0].replies <= threads[1].replies)

    def test_sorting_last_post_desc(self):
        """Sorting threads by last_post descendingly."""
        ThreadFactory(posts=[{}, {}, {}])
        PostFactory(created=datetime.now() - timedelta(days=1))
        threads = sort_threads(Thread.objects, 5, 1)
        self.assertTrue(threads[0].last_post.created >= threads[1].last_post.created)

    def test_thread_last_page(self):
        """Thread's last_page property is accurate."""
        t = ThreadFactory()
        # Format: (# replies, # of pages to expect)
        test_data = ((t.replies, 1),  # Test default
                     (50, 3),  # Test a large number
                     (19, 1),  # Test off-by-one error, low
                     (20, 2))  # Test off-by-one error, high
        for replies, pages in test_data:
            t.replies = replies
            eq_(t.last_page, pages)

    @raises(ThreadLockedError)
    def test_locked_thread(self):
        """Trying to reply to a locked thread should raise an exception."""
        locked = ThreadFactory(is_locked=True)
        user = UserFactory()
        # This should raise an exception
        locked.new_post(author=user, content='empty')

    def test_unlocked_thread(self):
        unlocked = ThreadFactory()
        user = UserFactory()
        # This should not raise an exception
        unlocked.new_post(author=user, content='empty')

    def test_post_no_session(self):
        r = get(self.client, 'forums.new_thread', kwargs={'forum_slug': 'test-forum'})
        assert(settings.LOGIN_URL in r.redirect_chain[0][0])
        eq_(302, r.redirect_chain[0][1])


class ThreadTestCase(ForumTestCase):

    def test_delete_no_session(self):
        """Delete a thread while logged out redirects."""
        r = get(self.client, 'forums.delete_thread',
                kwargs={'forum_slug': 'test-forum', 'thread_id': 1})
        assert(settings.LOGIN_URL in r.redirect_chain[0][0])
        eq_(302, r.redirect_chain[0][1])
