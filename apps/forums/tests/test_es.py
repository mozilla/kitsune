from forums.tests import ESTestCase
from forums.models import Post, Thread, Forum

from django.contrib.auth.models import User

import elasticutils
import uuid

from nose.tools import eq_


class TestPostUpdate(ESTestCase):
    def test_added(self):
        user = User.objects.get(pk=118533)
        original_count = elasticutils.S(Thread).count()

        # Creating a new Thread does create a new document in the
        # index.
        forum = Forum.objects.get(pk=1)
        new_thread = Thread(title=str(uuid.uuid4()), forum=forum,
                            creator_id=118533)

        eq_(elasticutils.S(Thread).count(), original_count)
        new_thread.save()
        self.refresh()

        eq_(elasticutils.S(Thread).count(), original_count + 1)

        new_post = Post(thread=new_thread, content=str(uuid.uuid4()),
                        author=user)

        eq_(elasticutils.S(Thread).count(), original_count + 1)

        new_post.save()
        self.refresh()

        eq_(elasticutils.S(Thread).count(), original_count + 1)

    def test_deleted(self):
        user = User.objects.get(pk=118533)
        original_count = elasticutils.S(Thread).count()

        # Creating a new Thread does create a new document in the
        # index.
        forum = Forum.objects.get(pk=1)
        new_thread = Thread(title=str(uuid.uuid4()), forum=forum,
                            creator_id=118533)

        eq_(elasticutils.S(Thread).count(), original_count)
        new_thread.save()
        self.refresh()

        eq_(elasticutils.S(Thread).count(), original_count + 1)

        new_post = Post(thread=new_thread, content=str(uuid.uuid4()),
                        author=user)

        eq_(elasticutils.S(Thread).count(), original_count + 1)

        new_post.save()
        self.refresh()

        eq_(elasticutils.S(Thread).count(), original_count + 1)

        new_thread.delete()
        self.refresh()

        eq_(elasticutils.S(Thread).count(), original_count)
