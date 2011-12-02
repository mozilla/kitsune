from forums.tests import ESTestCase
from forums.models import Post, Thread

from django.contrib.auth.models import User

import elasticutils
import uuid

from nose.tools import eq_


class TestPostUpdate(ESTestCase):
    def test_added(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        content = str(uuid.uuid4())

        thread = Thread.objects.get(pk=4)
        user = User.objects.get(pk=118533)

        # add a new post, then check that last_post is updated
        new_post = Post(thread=thread, content=content, author=user)

        original_count = elasticutils.S(Post).count()

        new_post.save()
        self.refresh()

        eq_(elasticutils.S(Post).count(), original_count + 1)

    def test_deleted(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        content = str(uuid.uuid4())

        thread = Thread.objects.get(pk=4)
        user = User.objects.get(pk=118533)

        # add a new post, then check that last_post is updated
        new_post = Post(thread=thread, content=content, author=user)

        original_count = elasticutils.S(Post).count()

        new_post.save()
        self.refresh()

        eq_(elasticutils.S(Post).count(), original_count + 1)

        new_post.delete()
        self.refresh()

        eq_(elasticutils.S(Post).count(), original_count)
