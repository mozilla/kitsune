from kitsune.kbforums.handlers import PostListener, ThreadListener
from kitsune.kbforums.tests import PostFactory, ThreadFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class TestThreadListener(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.sumo_bot = Profile.get_sumo_bot()
        self.listener = ThreadListener()

    def test_multiple_threads_reassignment(self):
        """Test that multiple threads are reassigned correctly."""
        thread1 = ThreadFactory(creator=self.user)
        thread2 = ThreadFactory(creator=self.user)
        thread3 = ThreadFactory(creator=self.user)

        self.listener.on_user_deletion(self.user)

        for thread in [thread1, thread2, thread3]:
            thread.refresh_from_db()
            self.assertEqual(thread.creator.username, self.sumo_bot.username)

    def test_other_users_threads_unaffected(self):
        """Test that other users' threads are not affected."""
        other_user = UserFactory()

        other_user = UserFactory()
        thread1 = ThreadFactory(creator=self.user)
        thread2 = ThreadFactory(creator=other_user)

        self.listener.on_user_deletion(self.user)

        thread1.refresh_from_db()
        thread2.refresh_from_db()
        self.assertEqual(thread1.creator.username, self.sumo_bot.username)
        self.assertEqual(thread2.creator, other_user)


class TestPostListener(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.sumo_bot = Profile.get_sumo_bot()
        self.listener = PostListener()

    def test_multiple_posts_reassignment(self):
        """Test that multiple posts are reassigned correctly."""
        post1 = PostFactory(creator=self.user)
        post2 = PostFactory(creator=self.user)
        post3 = PostFactory(creator=self.user)

        self.listener.on_user_deletion(self.user)

        for post in [post1, post2, post3]:
            post.refresh_from_db()
            self.assertEqual(post.creator.username, self.sumo_bot.username)

    def test_other_users_posts_unaffected(self):
        """Test that other users' posts are not affected."""
        other_user = UserFactory()
        post1 = PostFactory(creator=self.user)
        post2 = PostFactory(creator=other_user)

        self.listener.on_user_deletion(self.user)

        post1.refresh_from_db()
        post2.refresh_from_db()
        self.assertEqual(post1.creator.username, self.sumo_bot.username)
        self.assertEqual(post2.creator, other_user)
