from datetime import datetime, timedelta
from unittest.mock import Mock

from django.http import Http404
from pyquery import PyQuery as pq

from kitsune.forums.feeds import PostsFeed, ThreadsFeed
from kitsune.forums.tests import (
    ForumFactory,
    PostFactory,
    ThreadFactory,
)
from kitsune.sumo.tests import TestCase, get
from kitsune.users.tests import UserFactory


YESTERDAY = datetime.now() - timedelta(days=1)


class ForumTestFeeds(TestCase):
    def setUp(self):
        super(ForumTestFeeds, self).setUp()

    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        # Threads are sorted descending by last post date.
        f = ForumFactory()
        ThreadFactory(forum=f, created=YESTERDAY)
        t2 = ThreadFactory(forum=f)

        self.assertEqual(t2.id, ThreadsFeed().items(f)[0].id)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        t = ThreadFactory(posts__created=yesterday)
        p = PostFactory(thread=t, created=now)

        # The newest post should be the first one listed.
        self.assertEqual(p.id, PostsFeed().items(t)[0].id)

    def test_multi_feed_titling(self):
        """Ensure that titles are being applied properly to feeds."""
        t = ThreadFactory()
        forum = t.forum
        PostFactory(thread=t)

        response = get(self.client, "forums.threads", args=[forum.slug])
        doc = pq(response.content)
        self.assertEqual(
            ThreadsFeed().title(forum), doc('link[type="application/atom+xml"]')[0].attrib["title"]
        )

    def test_restricted_threads(self):
        """Ensure that threads are not shown unless permitted."""
        request = Mock()
        request.user = UserFactory()
        forum = ForumFactory(restrict_viewing=True)

        with self.assertRaisesMessage(Http404, ""):
            ThreadsFeed().get_object(request, forum.slug)

        request.user.is_superuser = True
        self.assertEqual(ThreadsFeed().get_object(request, forum.slug), forum)

    def test_restricted_posts(self):
        """Ensure that posts are not shown unless permitted."""
        request = Mock()
        request.user = UserFactory()
        forum = ForumFactory(restrict_viewing=True)
        thread = ThreadFactory(forum=forum)

        with self.assertRaisesMessage(Http404, ""):
            PostsFeed().get_object(request, forum.slug, thread.id)

        request.user.is_superuser = True
        self.assertEqual(PostsFeed().get_object(request, forum.slug, thread.id), thread)
