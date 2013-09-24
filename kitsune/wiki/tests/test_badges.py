from datetime import date

from django.conf import settings

from kitsune.kbadge.tests import badge
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import profile
from kitsune.wiki.badges import WIKI_BADGES
from kitsune.wiki.tests import revision, document


class TestWikiBadges(TestCase):

    def test_kb_badge(self):
        """Verify the KB Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = profile().user
        b = badge(
            slug=WIKI_BADGES['kb-badge']['slug'].format(year=year),
            title=WIKI_BADGES['kb-badge']['title'].format(year=year),
            description=WIKI_BADGES['kb-badge']['description'].format(
                year=year),
            save=True)

        # Create 9 approved en-US revisions.
        d = document(locale=settings.WIKI_DEFAULT_LANGUAGE, save=True)
        for i in range(9):
            revision(creator=u, document=d, is_approved=True, save=True)

        # User should NOT have the badge yet
        assert not b.is_awarded_to(u)

        # Create 1 more approved en-US revision.
        revision(creator=u, document=d, is_approved=True, save=True)

        # User should have the badge now
        assert b.is_awarded_to(u)

    def test_l10n_badge(self):
        """Verify the L10n Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = profile().user
        b = badge(
            slug=WIKI_BADGES['l10n-badge']['slug'].format(year=year),
            title=WIKI_BADGES['l10n-badge']['title'].format(year=year),
            description=WIKI_BADGES['l10n-badge']['description'].format(
                year=year),
            save=True)

        # Create 9 approved es revisions.
        d = document(locale='es', save=True)
        for i in range(9):
            revision(creator=u, document=d, is_approved=True, save=True)

        # User should NOT have the badge yet
        assert not b.is_awarded_to(u)

        # Create 1 more approved es revision.
        revision(creator=u, document=d, is_approved=True, save=True)

        # User should have the badge now
        assert b.is_awarded_to(u)
