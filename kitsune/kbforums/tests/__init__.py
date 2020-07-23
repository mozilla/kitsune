from django.conf import settings

import factory
from nose.tools import eq_

from kitsune.kbforums.models import Thread, Post, ThreadLockedError
from kitsune.kbforums.views import sort_threads
from kitsune.sumo.tests import get, LocalizingClient, TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import DocumentFactory


class ThreadFactory(factory.DjangoModelFactory):
    class Meta:
        model = Thread

    creator = factory.SubFactory(UserFactory)
    document = factory.SubFactory(DocumentFactory)


class PostFactory(factory.DjangoModelFactory):
    class Meta:
        model = Post

    creator = factory.SubFactory(UserFactory)
    thread = factory.SubFactory(ThreadFactory)


class KBForumTestCase(TestCase):
    client_class = LocalizingClient


class PostTestCase(KBForumTestCase):
    def test_new_post_updates_thread(self):
        """Saving a new post in a thread should update the last_post key in
        that thread to point to the new post."""
        t = ThreadFactory()
        post = t.new_post(creator=t.creator, content="an update")
        eq_(post.id, t.last_post_id)

    def test_update_post_does_not_update_thread(self):
        """Updating/saving an old post in a thread should _not_ update the
        last_post key in that thread."""
        p = PostFactory()
        old = p.thread.last_post_id
        p.content = "updated content"
        eq_(old, p.thread.last_post_id)

    def test_replies_count(self):
        """The Thread.replies value should remain one less than the number of
        posts in the thread."""
        t = ThreadFactory()
        old = t.replies
        t.new_post(creator=t.creator, content="test")
        eq_(old, t.replies)

    def test_sticky_threads_first(self):
        """Sticky threads should come before non-sticky threads."""
        ThreadFactory()
        t2 = ThreadFactory(is_sticky=True)
        s = Thread.objects.all()[0]
        eq_(t2.id, s.id)

    def test_thread_sorting(self):
        """After the sticky threads, threads should be sorted by the created
        date of the last post."""
        t1 = ThreadFactory(is_sticky=False)
        t1.post_set.create(creator=t1.creator, content="foo")
        t2 = ThreadFactory(is_sticky=False)
        t2.post_set.create(creator=t2.creator, content="bar")
        self.assertGreater(t2.last_post.created, t1.last_post.created)

    def test_post_sorting(self):
        """Posts should be sorted chronologically."""
        t = ThreadFactory()
        t.post_set.create(creator=t.creator, content="foo")
        t.post_set.create(creator=t.creator, content="bar")
        posts = t.post_set.all()
        for i in range(len(posts) - 1):
            self.assertLessEqual(posts[i].created, posts[i + 1].created)

    def test_sorting_creator(self):
        """Sorting threads by creator."""
        u1 = UserFactory(username="foo")
        u2 = UserFactory(username="bar")
        ThreadFactory(creator=u1)
        ThreadFactory(creator=u2)
        threads = sort_threads(Thread.objects, 3, 1)
        self.assertEqual(threads[0].creator.username, u1.username)
        self.assertEqual(threads[1].creator.username, u2.username)

    def test_sorting_replies(self):
        """Sorting threads by replies."""
        t1 = ThreadFactory()
        t1.new_post(t1.creator, "foo")
        t2 = ThreadFactory()
        t2.new_post(t2.creator, "bar")
        t2.new_post(t2.creator, "baz")
        threads = sort_threads(Thread.objects, 4)
        self.assertLessEqual(threads[0].replies, threads[1].replies)
        eq_(threads[0].replies, t1.replies)
        eq_(threads[1].replies, t2.replies)
        eq_(threads[0].title, t1.title)
        eq_(threads[1].title, t2.title)

    def test_sorting_last_post_desc(self):
        """Sorting threads by last_post descendingly."""
        t1 = ThreadFactory()
        t1.new_post(t1.creator, "foo")
        t2 = ThreadFactory()
        t2.new_post(t2.creator, "bar")
        threads = sort_threads(Thread.objects, 5, 1)
        self.assertGreaterEqual(threads[0].last_post.created, threads[1].last_post.created)

    def test_thread_last_page(self):
        """Thread's last_page property is accurate."""
        t = ThreadFactory()
        t.new_post(t.creator, "foo")
        # Format: (# replies, # of pages to expect)
        test_data = (
            (t.replies, 1),  # Test default
            (50, 3),  # Test a large number
            (19, 1),  # Test off-by-one error, low
            (20, 2),  # Test off-by-one error, high
        )
        for replies, pages in test_data:
            t.replies = replies
            eq_(t.last_page, pages)

    def test_locked_thread(self):
        """Trying to reply to a locked thread should raise an exception."""
        locked = ThreadFactory(is_locked=True)
        with self.assertRaises(ThreadLockedError):
            locked.new_post(creator=locked.creator, content="foo")

    def test_post_no_session(self):
        r = get(self.client, "wiki.discuss.new_thread", kwargs={"document_slug": "article-title"})
        assert settings.LOGIN_URL in r.redirect_chain[0][0]
        eq_(302, r.redirect_chain[0][1])


class ThreadTestCase(KBForumTestCase):
    def test_delete_no_session(self):
        """Delete a thread while logged out redirects."""
        r = get(
            self.client,
            "wiki.discuss.delete_thread",
            kwargs={"document_slug": "article-title", "thread_id": 1},
        )
        assert settings.LOGIN_URL in r.redirect_chain[0][0]
        eq_(302, r.redirect_chain[0][1])
