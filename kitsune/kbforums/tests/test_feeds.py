import time

from nose.tools import eq_
from pyquery import PyQuery as pq

from kitsune.kbforums.feeds import ThreadsFeed, PostsFeed
from kitsune.kbforums.tests import KBForumTestCase, get, thread
from kitsune.wiki.tests import document


class FeedSortingTestCase(KBForumTestCase):

    def test_threads_sort(self):
        """Ensure that threads are being sorted properly by date/time."""
        d = document(save=True)
        t = thread(document=d, save=True)
        t.new_post(creator=t.creator, content='foo')
        time.sleep(1)
        t2 = thread(document=d, save=True)
        t2.new_post(creator=t2.creator, content='foo')
        given_ = ThreadsFeed().items(d)[0].id
        eq_(t2.id, given_)

    def test_posts_sort(self):
        """Ensure that posts are being sorted properly by date/time."""
        t = thread(save=True)
        t.new_post(creator=t.creator, content='foo')
        time.sleep(1)
        p2 = t.new_post(creator=t.creator, content='foo')
        given_ = PostsFeed().items(t)[0].id
        eq_(p2.id, given_)

    def test_multi_feed_titling(self):
        """Ensure that titles are being applied properly to feeds."""
        d = document(save=True)
        response = get(self.client, 'wiki.discuss.threads', args=[d.slug])
        doc = pq(response.content)
        given_ = doc('link[type="application/atom+xml"]')[0].attrib['title']
        exp_ = ThreadsFeed().title(d)
        eq_(exp_, given_)
