import time

from pyquery import PyQuery as pq

from kitsune.kbforums.feeds import PostsFeed, ThreadsFeed
from kitsune.kbforums.tests import ThreadFactory, get
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class FeedSortingTestCase(TestCase):
    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        d = DocumentFactory()
        t = ThreadFactory(document=d)
        t.new_post(creator=t.creator, content="foo")
        time.sleep(1)
        t2 = ThreadFactory(document=d)
        t2.new_post(creator=t2.creator, content="foo")
        given_ = ThreadsFeed().items(d)[0].id
        self.assertEqual(t2.id, given_)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        t = ThreadFactory()
        t.new_post(creator=t.creator, content="foo")
        time.sleep(1)
        p2 = t.new_post(creator=t.creator, content="foo")
        given_ = PostsFeed().items(t)[0].id
        self.assertEqual(p2.id, given_)

    def test_multi_feed_titling(self):
        """Ensure that titles are being applied properly to feeds."""
        d = ApprovedRevisionFactory().document
        response = get(self.client, "wiki.discuss.threads", args=[d.slug])
        doc = pq(response.content)
        given_ = doc('link[type="application/atom+xml"]')[0].attrib["title"]
        exp_ = ThreadsFeed().title(d)
        self.assertEqual(exp_, given_)
