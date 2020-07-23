from datetime import datetime, timedelta
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.forums.feeds import ThreadsFeed, PostsFeed
from kitsune.forums.tests import ForumTestCase, ForumFactory, ThreadFactory, PostFactory
from kitsune.sumo.tests import get


YESTERDAY = datetime.now() - timedelta(days=1)


class ForumTestFeedSorting(ForumTestCase):
    def setUp(self):
        super(ForumTestFeedSorting, self).setUp()

    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        # Threads are sorted descending by last post date.
        f = ForumFactory()
        ThreadFactory(forum=f, created=YESTERDAY)
        t2 = ThreadFactory(forum=f)

        eq_(t2.id, ThreadsFeed().items(f)[0].id)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        t = ThreadFactory(posts__created=yesterday)
        p = PostFactory(thread=t, created=now)

        # The newest post should be the first one listed.
        eq_(p.id, PostsFeed().items(t)[0].id)

    def test_multi_feed_titling(self):
        """Ensure that titles are being applied properly to feeds."""
        t = ThreadFactory()
        forum = t.forum
        PostFactory(thread=t)

        response = get(self.client, "forums.threads", args=[forum.slug])
        doc = pq(response.content)
        eq_(
            ThreadsFeed().title(forum), doc('link[type="application/atom+xml"]')[0].attrib["title"]
        )
