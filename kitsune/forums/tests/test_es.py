from nose.tools import eq_

from kitsune.forums.models import ThreadMappingType
from kitsune.forums.tests import PostFactory
from kitsune.forums.tests import ThreadFactory
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.tests import UserFactory


class TestPostUpdate(ElasticTestCase):
    def test_added(self):
        # Nothing exists before the test starts
        eq_(ThreadMappingType.search().count(), 0)

        # Creating a new Thread does create a new document in the index.
        new_thread = ThreadFactory()
        self.refresh()
        eq_(ThreadMappingType.search().count(), 1)

        # Saving a new post in a thread doesn't create a new
        # document in the index.  Therefore, the count remains 1.
        #
        # TODO: This is ambiguous: it's not clear whether we correctly
        # updated the document in the index or whether the post_save
        # hook didn't kick off.  Need a better test.
        PostFactory(thread=new_thread)
        self.refresh()
        eq_(ThreadMappingType.search().count(), 1)

    def test_deleted(self):
        # Nothing exists before the test starts
        eq_(ThreadMappingType.search().count(), 0)

        # Creating a new Thread does create a new document in the index.
        new_thread = ThreadFactory()
        self.refresh()
        eq_(ThreadMappingType.search().count(), 1)

        # Deleting the thread deletes the document in the index.
        new_thread.delete()
        self.refresh()
        eq_(ThreadMappingType.search().count(), 0)

    def test_thread_is_reindexed_on_username_change(self):
        search = ThreadMappingType.search()

        u = UserFactory(username='dexter')
        ThreadFactory(creator=u, title='Hello')

        self.refresh()
        eq_(search.query(post_title='hello')[0]['post_author_ord'], ['dexter'])

        # Change the username and verify the index.
        u.username = 'walter'
        u.save()
        self.refresh()
        eq_(search.query(post_title='hello')[0]['post_author_ord'], ['walter'])
