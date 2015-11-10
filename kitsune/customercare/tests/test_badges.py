from datetime import date

from kitsune.customercare.badges import AOA_BADGE
from kitsune.customercare.tests import ReplyFactory
from kitsune.kbadge.tests import BadgeFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.customercare.badges import register_signals


class TestAOABadges(TestCase):

    def setUp(self):
        # Make sure the badges hear this.
        register_signals()

    def test_aoa_badge(self):
        """Verify the KB Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = UserFactory()
        b = BadgeFactory(
            slug=AOA_BADGE['slug'].format(year=year),
            title=AOA_BADGE['title'].format(year=year),
            description=AOA_BADGE['description'].format(year=year))

        # Create 49 replies.
        for _ in range(49):
            ReplyFactory(user=u)

        # User should NOT have the badge yet.
        assert not b.is_awarded_to(u)

        # Create 1 more reply.
        ReplyFactory(user=u)

        # User should have the badge now.
        assert b.is_awarded_to(u)
