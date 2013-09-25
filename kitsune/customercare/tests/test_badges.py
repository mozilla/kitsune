from datetime import date

from kitsune.customercare.badges import AOA_BADGE
from kitsune.customercare.tests import reply
from kitsune.kbadge.tests import badge
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import profile


class TestAOABadges(TestCase):

    def test_aoa_badge(self):
        """Verify the KB Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = profile().user
        b = badge(
            slug=AOA_BADGE['slug'].format(year=year),
            title=AOA_BADGE['title'].format(year=year),
            description=AOA_BADGE['description'].format(year=year),
            save=True)

        # Create 49 replies.
        for i in range(49):
            reply(user=u, save=True)

        # User should NOT have the badge yet.
        assert not b.is_awarded_to(u)

        # Create 1 more reply.
        reply(user=u, save=True)

        # User should have the badge now.
        assert b.is_awarded_to(u)
