from django.contrib.contenttypes.models import ContentType

from kitsune.flagit.handlers import FlagListener
from kitsune.flagit.models import FlaggedObject
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class TestFlagListener(TestCase):
    def setUp(self):
        self.flagged_user = UserFactory()
        self.listener = FlagListener()

    def test_user_flags_deletion(self):
        """Test that flags against a deleted user are removed."""
        reporting_user1 = UserFactory()
        reporting_user2 = UserFactory()

        user_content_type = ContentType.objects.get_for_model(Profile)
        flag1 = FlaggedObject.objects.create(
            content_type=user_content_type,
            object_id=self.flagged_user.id,
            creator=reporting_user1,
            reason=FlaggedObject.REASON_SPAM,
        )
        flag2 = FlaggedObject.objects.create(
            content_type=user_content_type,
            object_id=self.flagged_user.id,
            creator=reporting_user2,
            reason=FlaggedObject.REASON_ABUSE,
        )

        other_flagged_user = UserFactory()
        other_reporting_user = UserFactory()
        flag3 = FlaggedObject.objects.create(
            content_type=user_content_type,
            object_id=other_flagged_user.id,
            creator=other_reporting_user,
            reason=FlaggedObject.REASON_SPAM,
        )

        self.listener.on_user_deletion(self.flagged_user)

        self.assertFalse(FlaggedObject.objects.filter(id=flag1.id).exists())
        self.assertFalse(FlaggedObject.objects.filter(id=flag2.id).exists())
        self.assertTrue(FlaggedObject.objects.filter(id=flag3.id).exists())

    def test_flags_created_by_user_remain(self):
        """Test that flags created by the deleted user remain."""
        user_to_be_flagged = UserFactory()
        user_content_type = ContentType.objects.get_for_model(Profile)

        flag1 = FlaggedObject.objects.create(
            content_type=user_content_type,
            object_id=user_to_be_flagged.id,
            creator=self.flagged_user,
            reason=FlaggedObject.REASON_SPAM,
        )

        self.listener.on_user_deletion(self.flagged_user)
        self.assertTrue(FlaggedObject.objects.filter(id=flag1.id).exists())

    def test_multiple_content_types(self):
        """Test that only flags against the user are deleted, not flags of other content types."""
        reporting_user = UserFactory()
        user_content_type = ContentType.objects.get_for_model(Profile)

        flag1 = FlaggedObject.objects.create(
            content_type=user_content_type,
            object_id=self.flagged_user.id,
            creator=reporting_user,
            reason=FlaggedObject.REASON_SPAM,
        )

        other_reporting_user = UserFactory()
        flag2 = FlaggedObject.objects.create(
            content_type=ContentType.objects.get_for_model(FlaggedObject),
            object_id=flag1.id,
            creator=other_reporting_user,
            reason=FlaggedObject.REASON_OTHER,
        )

        self.listener.on_user_deletion(self.flagged_user)

        self.assertFalse(FlaggedObject.objects.filter(id=flag1.id).exists())
        self.assertTrue(FlaggedObject.objects.filter(id=flag2.id).exists())
