import uuid

import elasticutils
from nose.tools import eq_

from forums.models import Post, Thread
from forums.tests import forum
from sumo.tests import ElasticTestCase
from users.tests import get_user


class TestPostUpdate(ElasticTestCase):
    def test_added(self):
        user = get_user()

        new_thread = Thread(title=str(uuid.uuid4()), forum=forum(save=True),
                            creator=user)
        eq_(elasticutils.S(Thread).count(), 0)

        # Saving a new Thread does create a new document in the
        # index.
        new_thread.save()
        self.refresh()
        eq_(elasticutils.S(Thread).count(), 1)

        new_post = Post(thread=new_thread, content=str(uuid.uuid4()),
                        author=user)
        eq_(elasticutils.S(Thread).count(), 1)

        new_post.save()
        self.refresh()

        # Saving a new post in a thread doesn't create a new
        # document in the index.  Therefore, the count remains 1.
        #
        # TODO: This is ambiguous: it's not clear whether we correctly
        # updated the document in the index or whether the post_save
        # hook didn't kick off.  Need a better test.
        eq_(elasticutils.S(Thread).count(), 1)

    def test_deleted(self):
        user = get_user()

        new_thread = Thread(title=str(uuid.uuid4()), forum=forum(save=True),
                            creator=user)
        eq_(elasticutils.S(Thread).count(), 0)

        # Saving a new Thread does create a new document in the
        # index.
        new_thread.save()
        self.refresh()
        eq_(elasticutils.S(Thread).count(), 1)

        new_post = Post(thread=new_thread, content=str(uuid.uuid4()),
                        author=user)
        eq_(elasticutils.S(Thread).count(), 1)

        new_post.save()
        self.refresh()
        eq_(elasticutils.S(Thread).count(), 1)

        new_thread.delete()
        self.refresh()
        eq_(elasticutils.S(Thread).count(), 0)
