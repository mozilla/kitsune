from nose.tools import eq_

from kitsune.forums.models import ThreadMappingType
from kitsune.forums.tests import thread, post
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.tests import user


class TestPostUpdate(ElasticTestCase):
    def test_added(self):
        new_thread = thread()
        eq_(ThreadMappingType.search().count(), 0)

        # Saving a new Thread does create a new document in the
        # index.
        new_thread.save()
        self.refresh()
        eq_(ThreadMappingType.search().count(), 1)

        new_post = post(thread=new_thread)
        eq_(ThreadMappingType.search().count(), 1)

        new_post.save()
        self.refresh()

        # Saving a new post in a thread doesn't create a new
        # document in the index.  Therefore, the count remains 1.
        #
        # TODO: This is ambiguous: it's not clear whether we correctly
        # updated the document in the index or whether the post_save
        # hook didn't kick off.  Need a better test.
        eq_(ThreadMappingType.search().count(), 1)

    def test_deleted(self):
        new_thread = thread()
        eq_(ThreadMappingType.search().count(), 0)

        # Saving a new Thread does create a new document in the
        # index.
        new_thread.save()
        self.refresh()
        eq_(ThreadMappingType.search().count(), 1)

        new_post = post(thread=new_thread)
        eq_(ThreadMappingType.search().count(), 1)

        new_post.save()
        self.refresh()
        eq_(ThreadMappingType.search().count(), 1)

        new_thread.delete()
        self.refresh()
        eq_(ThreadMappingType.search().count(), 0)

    def test_thread_is_reindexed_on_username_change(self):
        search = ThreadMappingType.search()

        u = user(username='dexter', save=True)

        t = thread(creator=u, title=u'Hello', save=True)
        post(author=u, thread=t, save=True)
        self.refresh()
        eq_(search.query(post_title='hello')[0]['post_author_ord'],
            [u'dexter'])

        # Change the username and verify the index.
        u.username = 'walter'
        u.save()
        self.refresh()
        eq_(search.query(post_title='hello')[0]['post_author_ord'],
            [u'walter'])
