from nose.tools import eq_

from forums.models import Thread
from forums.tests import thread, post
from search.tests.test_es import ElasticTestCase


class TestPostUpdate(ElasticTestCase):
    def test_added(self):
        new_thread = thread()
        eq_(Thread.search().count(), 0)

        # Saving a new Thread does create a new document in the
        # index.
        new_thread.save()
        self.refresh()
        eq_(Thread.search().count(), 1)

        new_post = post(thread=new_thread)
        eq_(Thread.search().count(), 1)

        new_post.save()
        self.refresh()

        # Saving a new post in a thread doesn't create a new
        # document in the index.  Therefore, the count remains 1.
        #
        # TODO: This is ambiguous: it's not clear whether we correctly
        # updated the document in the index or whether the post_save
        # hook didn't kick off.  Need a better test.
        eq_(Thread.search().count(), 1)

    def test_deleted(self):
        new_thread = thread()
        eq_(Thread.search().count(), 0)

        # Saving a new Thread does create a new document in the
        # index.
        new_thread.save()
        self.refresh()
        eq_(Thread.search().count(), 1)

        new_post = post(thread=new_thread)
        eq_(Thread.search().count(), 1)

        new_post.save()
        self.refresh()
        eq_(Thread.search().count(), 1)

        new_thread.delete()
        self.refresh()
        eq_(Thread.search().count(), 0)
