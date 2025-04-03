from kitsune.flagit.models import FlaggedObject
from kitsune.forums.models import Post
from kitsune.forums.tests import PostFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class FlaggedObjectTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.system_user = UserFactory()
        self.system_user.profile.account_type = Profile.AccountType.SYSTEM
        self.system_user.profile.save()
        self.system_user_post = PostFactory(author=self.system_user)
        self.post = PostFactory()

    def test_save_with_deletion(self):
        """Test save that triggers deletion when conditions are met"""
        flag = FlaggedObject.objects.create(
            status=FlaggedObject.FLAG_PENDING,
            content_object=self.system_user_post,
            creator=self.user,
        )

        self.assertTrue(FlaggedObject.objects.filter(id=flag.id).exists())
        flag.status = FlaggedObject.FLAG_ACCEPTED
        flag.save()
        self.assertFalse(FlaggedObject.objects.filter(id=flag.id).exists())
        self.assertFalse(Post.objects.filter(id=self.system_user_post.id).exists())

    def test_save_with_accepted_non_system_user(self):
        """Test save with accepted status but non-system user"""
        flag = FlaggedObject.objects.create(
            status=FlaggedObject.FLAG_ACCEPTED,
            content_object=self.post,
            creator=self.user,
        )
        self.assertTrue(Post.objects.filter(id=self.post.id).exists())
        self.assertTrue(FlaggedObject.objects.filter(id=flag.id).exists())

    def test_save_with_system_user_non_accepted(self):
        """Test save with system user but non-accepted status"""
        flag = FlaggedObject.objects.create(
            status=FlaggedObject.FLAG_PENDING,
            content_object=self.system_user_post,
            creator=self.user,
        )

        self.assertTrue(Post.objects.filter(id=self.system_user_post.id).exists())
        self.assertTrue(FlaggedObject.objects.filter(id=flag.id).exists())
