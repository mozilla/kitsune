from django.conf import settings

from kitsune.kbadge.handlers import AwardListener, BadgeListener
from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class TestAwardListener(TestCase):

    def setUp(self):
        self.user = UserFactory()
        Profile.get_sumo_bot()
        self.listener = AwardListener()

    def test_award_creator_replacement(self):
        award1 = AwardFactory()
        award2 = AwardFactory(creator=self.user)
        creator = UserFactory()
        award3 = AwardFactory(creator=creator)

        self.listener.on_user_deletion(self.user)

        award1.refresh_from_db()
        award2.refresh_from_db()
        award3.refresh_from_db()

        self.assertIs(award1.creator, None)
        self.assertEqual(award2.creator.username, settings.SUMO_BOT_USERNAME)
        self.assertEqual(award3.creator.username, creator.username)


class TestBadgeListener(TestCase):

    def setUp(self):
        self.user = UserFactory()
        Profile.get_sumo_bot()
        self.listener = BadgeListener()

    def test_badge_creator_replacement(self):
        badge1 = BadgeFactory()
        badge2 = BadgeFactory(creator=self.user)
        creator = UserFactory()
        badge3 = BadgeFactory(creator=creator)

        self.listener.on_user_deletion(self.user)

        badge1.refresh_from_db()
        badge2.refresh_from_db()
        badge3.refresh_from_db()

        self.assertIs(badge1.creator, None)
        self.assertEqual(badge2.creator.username, settings.SUMO_BOT_USERNAME)
        self.assertEqual(badge3.creator.username, creator.username)
