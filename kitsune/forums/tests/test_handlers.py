from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from kitsune.flagit.models import FlaggedObject
from kitsune.forums.handlers import PostListener, ThreadListener
from kitsune.forums.models import Post
from kitsune.forums.tests import PostFactory, ThreadFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class TestThreadListener(TestCase):
    def setUp(self):
        self.user = UserFactory()
        User.objects.get_or_create(username=settings.SUMO_BOT_USERNAME)
        self.listener = ThreadListener()

    def test_multiple_threads_reassignment(self):
        """Test that multiple threads are reassigned correctly."""
        thread1 = ThreadFactory(creator=self.user)
        thread2 = ThreadFactory(creator=self.user)
        thread3 = ThreadFactory(creator=self.user)

        self.listener.on_user_deletion(self.user)

        for thread in [thread1, thread2, thread3]:
            thread.refresh_from_db()
            self.assertEqual(thread.creator.username, settings.SUMO_BOT_USERNAME)

    def test_other_users_threads_unaffected(self):
        """Test that other users' threads are not affected."""
        other_user = UserFactory()
        thread1 = ThreadFactory(creator=self.user)
        thread2 = ThreadFactory(creator=other_user)

        self.listener.on_user_deletion(self.user)

        thread1.refresh_from_db()
        thread2.refresh_from_db()
        self.assertEqual(thread1.creator.username, settings.SUMO_BOT_USERNAME)
        self.assertEqual(thread2.creator, other_user)


class TestPostListener(TestCase):
    def setUp(self):
        self.user = UserFactory()
        User.objects.get_or_create(username=settings.SUMO_BOT_USERNAME)
        self.listener = PostListener()

    def test_multiple_posts_reassignment(self):
        """Test that multiple posts are reassigned correctly."""
        post1 = PostFactory(author=self.user)
        post2 = PostFactory(author=self.user)
        post3 = PostFactory(author=self.user)
        post4 = PostFactory(updated_by=self.user)
        post5 = PostFactory(updated_by=self.user)

        self.listener.on_user_deletion(self.user)

        for post in [post1, post2, post3]:
            post.refresh_from_db()
            self.assertEqual(post.author.username, settings.SUMO_BOT_USERNAME)

        for post in [post4, post5]:
            post.refresh_from_db()
            self.assertEqual(post.updated_by.username, settings.SUMO_BOT_USERNAME)

    def test_other_users_posts_unaffected(self):
        """Test that other users' posts are not affected."""
        other_user = UserFactory()
        post1 = PostFactory(author=self.user, updated_by=other_user)
        post2 = PostFactory(author=other_user, updated_by=other_user)
        post3 = PostFactory(author=other_user, updated_by=self.user)

        self.listener.on_user_deletion(self.user)

        for post in [post1, post2, post3]:
            post.refresh_from_db()

        self.assertEqual(post1.author.username, settings.SUMO_BOT_USERNAME)
        self.assertEqual(post1.updated_by, other_user)
        self.assertEqual(post2.author, other_user)
        self.assertEqual(post2.updated_by, other_user)
        self.assertEqual(post3.author, other_user)
        self.assertEqual(post3.updated_by.username, settings.SUMO_BOT_USERNAME)

    def test_flagged_posts_deletion(self):
        """Test that flagged posts are deleted."""
        post1 = PostFactory(author=self.user)
        post2 = PostFactory(author=self.user)
        post3 = PostFactory(author=self.user)
        post4 = PostFactory(updated_by=self.user)

        post_content_type = ContentType.objects.get_for_model(Post)

        FlaggedObject.objects.create(
            content_type=post_content_type,
            object_id=post1.id,
            creator=UserFactory(),
            reason=FlaggedObject.REASON_SPAM,
        )
        FlaggedObject.objects.create(
            content_type=post_content_type,
            object_id=post2.id,
            creator=UserFactory(),
            reason=FlaggedObject.REASON_SPAM,
        )

        self.listener.on_user_deletion(self.user)

        with self.assertRaises(Post.DoesNotExist):
            post1.refresh_from_db()
        with self.assertRaises(Post.DoesNotExist):
            post2.refresh_from_db()

        post3.refresh_from_db()
        self.assertEqual(post3.author.username, settings.SUMO_BOT_USERNAME)
        post4.refresh_from_db()
        self.assertEqual(post4.updated_by.username, settings.SUMO_BOT_USERNAME)
