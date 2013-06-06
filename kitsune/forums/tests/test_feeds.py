from datetime import datetime, timedelta
from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.forums.feeds import ThreadsFeed, PostsFeed
from kitsune.forums.tests import ForumTestCase, forum, thread, post
from kitsune.sumo.tests import get


YESTERDAY = datetime.now() - timedelta(days=1)


class ForumTestFeedSorting(ForumTestCase):

    def setUp(self):
        super(ForumTestFeedSorting, self).setUp()

    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        # Threads are sorted descending by last post date.
        f = forum(save=True)
        t1 = thread(forum=f, created=YESTERDAY, save=True)
        post(thread=t1, created=YESTERDAY, save=True)
        t2 = thread(forum=f, save=True)
        post(thread=t2, save=True)

        eq_(t2.id, ThreadsFeed().items(f)[0].id)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        t = thread(save=True)
        post(thread=t, created=YESTERDAY, save=True)
        post(thread=t, created=YESTERDAY, save=True)
        p = post(thread=t, save=True)

        # The newest post should be the first one listed.
        eq_(p.id, PostsFeed().items(t)[0].id)

    def test_multi_feed_titling(self):
        """Ensure that titles are being applied properly to feeds."""
        t = thread(save=True)
        forum = t.forum
        post(thread=t, save=True)

        response = get(self.client, 'forums.threads', args=[forum.slug])
        doc = pq(response.content)
        eq_(ThreadsFeed().title(forum),
            doc('link[type="application/atom+xml"]')[0].attrib['title'])
