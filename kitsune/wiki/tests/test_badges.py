from contextlib import suppress
from datetime import date
from unittest.mock import patch

from django.conf import settings
from django.db import DatabaseError, transaction

from kitsune.kbadge.tests import BadgeFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.badges import WIKI_BADGES, on_revision_save
from kitsune.wiki.models import Revision
from kitsune.wiki.tests import (
    ApprovedRevisionFactory,
    DocumentFactory,
    RevisionFactory,
    run_badge_checks_now,
)


class BadgeCheckTimingTests(TestCase):
    def test_badge_checks_are_queued_on_commit(self):
        revision = ApprovedRevisionFactory(reviewer=UserFactory())

        with patch("kitsune.wiki.tasks.maybe_award_badge.delay") as award:
            with self.captureOnCommitCallbacks() as callbacks:
                on_revision_save(sender=Revision, instance=revision)
            award.assert_not_called()
            for callback in callbacks:
                callback()
            self.assertEqual(award.call_count, 2)

            award.reset_mock()
            with self.captureOnCommitCallbacks() as callbacks:
                with suppress(DatabaseError), transaction.atomic():
                    on_revision_save(sender=Revision, instance=revision)
                    raise DatabaseError
            self.assertEqual(callbacks, [])
            award.assert_not_called()


@run_badge_checks_now
class TestWikiBadges(TestCase):
    def test_kb_badge(self):
        """Verify the KB Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = UserFactory()
        b = BadgeFactory(
            slug=WIKI_BADGES["kb-badge"]["slug"].format(year=year),
            title=WIKI_BADGES["kb-badge"]["title"].format(year=year),
            description=WIKI_BADGES["kb-badge"]["description"].format(year=year),
        )

        # Create 9 approved en-US revisions.
        d = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        ApprovedRevisionFactory.create_batch(
            settings.BADGE_LIMIT_L10N_KB - 1, creator=u, document=d
        )

        # User should NOT have the badge yet
        assert not b.is_awarded_to(u)

        # Create 1 more approved en-US revision.
        RevisionFactory(creator=u, document=d, is_approved=True)

        # User should have the badge now
        assert b.is_awarded_to(u)

    def test_l10n_badge(self):
        """Verify the L10n Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        user = UserFactory()
        b = BadgeFactory(
            slug=WIKI_BADGES["l10n-badge"]["slug"].format(year=year),
            title=WIKI_BADGES["l10n-badge"]["title"].format(year=year),
            description=WIKI_BADGES["l10n-badge"]["description"].format(year=year),
        )

        # Create 9 approved es revisions.
        doc = DocumentFactory(locale="es")
        ApprovedRevisionFactory.create_batch(
            settings.BADGE_LIMIT_L10N_KB - 1, creator=user, document=doc
        )

        # User should NOT have the badge yet
        assert not b.is_awarded_to(user)

        # Create 1 more approved es revision.
        RevisionFactory(creator=user, document=doc, is_approved=True)

        # User should have the badge now
        assert b.is_awarded_to(user)

    def test_reviewer_badge(self):
        """Verify the Reviewer Badge is awarded properly."""
        # Create the user and badge.
        year = date.today().year
        u = UserFactory()
        b = BadgeFactory(
            slug=WIKI_BADGES["reviewer-badge"]["slug"].format(year=year),
            title=WIKI_BADGES["reviewer-badge"]["title"].format(year=year),
            description=WIKI_BADGES["reviewer-badge"]["description"].format(year=year),
        )

        # Create 24 en-US revisions approved by the user.
        d = DocumentFactory(locale=settings.WIKI_DEFAULT_LANGUAGE)
        ApprovedRevisionFactory.create_batch(
            settings.BADGE_LIMIT_REVIEWER - 1, reviewer=u, document=d
        )

        # User should NOT have the badge yet
        assert not b.is_awarded_to(u)

        # Create 1 more en-US revision approved by the user.
        ApprovedRevisionFactory(reviewer=u, document=d)

        # User should have the badge now
        assert b.is_awarded_to(u)
