from django.conf import settings

from nose.tools import eq_

from kitsune.kbforums.models import Thread, Post, ThreadLockedError
from kitsune.kbforums.views import sort_threads
from kitsune.sumo.tests import get, LocalizingClient, TestCase, with_save
from kitsune.users.tests import user
from kitsune.wiki.tests import document


@with_save
def thread(**kwargs):
    defaults = {}
    if 'document' not in kwargs:
        defaults['document'] = document(save=True)
    if 'creator' not in kwargs:
        defaults['creator'] = user(save=True)
    defaults.update(kwargs)
    return Thread(**defaults)


@with_save
def post(**kwargs):
    defaults = {}
    if 'creator' not in kwargs:
        defaults['creator'] = user(save=True)
    if 'thread' not in kwargs:
        defaults['thread'] = thread(creator=defaults['creator'], save=True)
    defaults.update(kwargs)
    return Post(**defaults)


class KBForumTestCase(TestCase):
    client_class = LocalizingClient


class PostTestCase(KBForumTestCase):

    def test_new_post_updates_thread(self):
        """Saving a new post in a thread should update the last_post key in
        that thread to point to the new post."""
        t = thread(save=True)
        post = t.new_post(creator=t.creator, content='an update')
        eq_(post.id, t.last_post_id)

    def test_update_post_does_not_update_thread(self):
        """Updating/saving an old post in a thread should _not_ update the
        last_post key in that thread."""
        p = post(save=True)
        old = p.thread.last_post_id
        p.content = 'updated content'
        eq_(old, p.thread.last_post_id)

    def test_replies_count(self):
        """The Thread.replies value should remain one less than the number of
        posts in the thread."""
        t = thread(save=True)
        old = t.replies
        t.new_post(creator=t.creator, content='test')
        eq_(old, t.replies)

    def test_sticky_threads_first(self):
        """Sticky threads should come before non-sticky threads."""
        thread(save=True)
        t2 = thread(is_sticky=True, save=True)
        s = Thread.objects.all()[0]
        eq_(t2.id, s.id)

    def test_thread_sorting(self):
        """After the sticky threads, threads should be sorted by the created
        date of the last post."""
        t1 = thread(is_sticky=False, save=True)
        t1.post_set.create(creator=t1.creator, content='foo')
        t2 = thread(is_sticky=False, save=True)
        t2.post_set.create(creator=t2.creator, content='bar')
        self.assertGreater(t2.last_post.created, t1.last_post.created)

    def test_post_sorting(self):
        """Posts should be sorted chronologically."""
        t = thread(save=True)
        t.post_set.create(creator=t.creator, content='foo')
        t.post_set.create(creator=t.creator, content='bar')
        posts = t.post_set.all()
        for i in range(len(posts) - 1):
            self.assertLessEqual(posts[i].created,
                                 posts[i + 1].created)

    def test_sorting_creator(self):
        """Sorting threads by creator."""
        u1 = user(username='foo', save=True)
        u2 = user(username='bar', save=True)
        thread(creator=u1, save=True)
        thread(creator=u2, save=True)
        threads = sort_threads(Thread.objects, 3, 1)
        self.assertEqual(threads[0].creator.username, u1.username)
        self.assertEqual(threads[1].creator.username, u2.username)

    def test_sorting_replies(self):
        """Sorting threads by replies."""
        t1 = thread(save=True)
        t1.new_post(t1.creator, 'foo')
        t2 = thread(save=True)
        t2.new_post(t2.creator, 'bar')
        t2.new_post(t2.creator, 'baz')
        threads = sort_threads(Thread.objects, 4)
        self.assertLessEqual(threads[0].replies,
                             threads[1].replies)
        eq_(threads[0].replies, t1.replies)
        eq_(threads[1].replies, t2.replies)
        eq_(threads[0].title, t1.title)
        eq_(threads[1].title, t2.title)

    def test_sorting_last_post_desc(self):
        """Sorting threads by last_post descendingly."""
        t1 = thread(save=True)
        t1.new_post(t1.creator, 'foo')
        t2 = thread(save=True)
        t2.new_post(t2.creator, 'bar')
        threads = sort_threads(Thread.objects, 5, 1)
        self.assertGreaterEqual(threads[0].last_post.created,
                                threads[1].last_post.created)

    def test_thread_last_page(self):
        """Thread's last_page property is accurate."""
        t = thread(save=True)
        t.new_post(t.creator, 'foo')
        # Format: (# replies, # of pages to expect)
        test_data = ((t.replies, 1),  # Test default
                     (50, 3),  # Test a large number
                     (19, 1),  # Test off-by-one error, low
                     (20, 2),  # Test off-by-one error, high
                     )
        for replies, pages in test_data:
            t.replies = replies
            eq_(t.last_page, pages)

    def test_locked_thread(self):
        """Trying to reply to a locked thread should raise an exception."""
        locked = thread(is_locked=True, save=True)
        with self.assertRaises(ThreadLockedError):
            locked.new_post(creator=locked.creator, content='foo')

    def test_post_no_session(self):
        r = get(self.client, 'wiki.discuss.new_thread',
                kwargs={'document_slug': 'article-title'})
        assert(settings.LOGIN_URL in r.redirect_chain[0][0])
        eq_(302, r.redirect_chain[0][1])


class ThreadTestCase(KBForumTestCase):

    def test_delete_no_session(self):
        """Delete a thread while logged out redirects."""
        r = get(self.client, 'wiki.discuss.delete_thread',
                kwargs={'document_slug': 'article-title', 'thread_id': 1})
        assert(settings.LOGIN_URL in r.redirect_chain[0][0])
        eq_(302, r.redirect_chain[0][1])
