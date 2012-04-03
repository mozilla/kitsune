from datetime import datetime, timedelta
from nose.tools import eq_
from pyquery import PyQuery as pq

from forums.feeds import ThreadsFeed, PostsFeed
from forums.tests import ForumTestCase, thread, post
from sumo.tests import get


class ForumTestFeedSorting(ForumTestCase):

    def setUp(self):
        super(ForumTestFeedSorting, self).setUp()

    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        t = thread(save=True)
        f = t.forum

        eq_(f.id, ThreadsFeed().items(f)[0].id)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        t = thread(save=True)
        yesterday = datetime.now() - timedelta(days=1)
        post(thread=t, created=yesterday, save=True)
        post(thread=t, created=yesterday, save=True)
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
        eq_(doc('link[type="application/atom+xml"]')[0].attrib['title'],
            ThreadsFeed().title(forum))
