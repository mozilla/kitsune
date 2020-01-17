from django.core import mail

from nose.tools import eq_

from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.sumo.tests import TestCase


class AwardNotificationTests(TestCase):
    def test_notification(self):
        # Note: Need to do this import here so the
        # notify_award_recipient function handles the
        # badge_was_awarded signal. This works fine in production
        # because badges gets loaded by kitsune.kbadge in startup.
        from kitsune.kbadge import badges  # noqa

        new_badge = BadgeFactory()

        # Check the mail queue first.
        eq_(0, len(mail.outbox))

        # Create an award and save it. This triggers the notification.
        AwardFactory(description='yay!', badge=new_badge)

        eq_(1, len(mail.outbox))

        # TODO: test contents--not doing that now because it's a
        # mockup.
