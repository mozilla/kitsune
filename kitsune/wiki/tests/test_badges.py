from contextlib import suppress
from unittest.mock import patch

from django.db import DatabaseError, transaction

from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.badges import on_revision_save
from kitsune.wiki.models import Revision
from kitsune.wiki.tests import ApprovedRevisionFactory


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
