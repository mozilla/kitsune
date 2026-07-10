from django.core import mail
from django.test import override_settings

from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.templatetags.jinja_helpers import display_name
from kitsune.users.tests import UserFactory


class AwardNotificationTests(TestCase):
    def test_notification(self):
        # Note: Need to do this import here so the
        # notify_award_recipient function handles the
        # badge_was_awarded signal. This works fine in production
        # because badges gets loaded by kitsune.kbadge in startup.
        from kitsune.kbadge import badges  # noqa

        new_badge = BadgeFactory()

        # Check the mail queue first.
        self.assertEqual(0, len(mail.outbox))

        # Create an award and save it. This triggers the notification.
        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description="yay!", badge=new_badge)

        self.assertEqual(1, len(mail.outbox))

    def test_notification_contents(self):
        from kitsune.kbadge import badges  # noqa

        badge = BadgeFactory(title="Test Badge", description="Test Badge description")

        # Check the mail queue first.
        self.assertEqual(0, len(mail.outbox))

        # Create an award without description.
        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description="", badge=badge)

        self.assertEqual(1, len(mail.outbox))
        self.assertIn("You were awarded the 'Test Badge' badge!", mail.outbox[0].subject)
        self.assertIn("Congratulations!", mail.outbox[0].body)
        self.assertIn("You have been awarded the Test Badge badge!", mail.outbox[0].body)
        # The email should include the badge description in such case.
        self.assertIn("Test Badge description", mail.outbox[0].body)
        self.assertIn("Mozilla Support is made possible by volunteers like you. "
                      "Thank you for the time, knowledge, and care you've shared with the community.",
                      mail.outbox[0].body)
        self.assertIn("Your badges are displayed on your profile page. Check it out:", mail.outbox[0].body)

        # Create an award with description.
        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description="Award description", badge=badge)

        self.assertEqual(2, len(mail.outbox))
        self.assertIn("You were awarded the 'Test Badge' badge!", mail.outbox[1].subject)
        self.assertIn("Congratulations!", mail.outbox[1].body)
        self.assertIn("You have been awarded the Test Badge badge!", mail.outbox[1].body)
        # The email should include the award description in such case.
        self.assertIn("Award description", mail.outbox[1].body)
        # The email should NOT include the badge description in such case.
        self.assertNotIn("Test Badge description", mail.outbox[1].body)
        self.assertIn("Mozilla Support is made possible by volunteers like you. "
                      "Thank you for the time, knowledge, and care you've shared with the community.",
                      mail.outbox[1].body)
        self.assertIn("Your badges are displayed on your profile page. Check it out:", mail.outbox[1].body)

        # Create an award with description and awarder.
        awarder = UserFactory()
        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description="Award description", creator=awarder, badge=badge)

        self.assertEqual(3, len(mail.outbox))
        self.assertIn("You were awarded the 'Test Badge' badge!", mail.outbox[2].subject)
        self.assertIn("Congratulations!", mail.outbox[2].body)
        # The email should mention the awarder in such case.
        self.assertIn(f"{display_name(awarder)} has awarded you the Test Badge badge!", mail.outbox[2].body)
        # The generic award message should NOT appear.
        self.assertNotIn("You have been awarded", mail.outbox[2].body)
        # The email should include the award description in such case.
        self.assertIn("Award description", mail.outbox[2].body)
        # The email should NOT include the badge description in such case.
        self.assertNotIn("Test Badge description", mail.outbox[2].body)
        self.assertIn("Mozilla Support is made possible by volunteers like you. "
                      "Thank you for the time, knowledge, and care you've shared with the community.",
                      mail.outbox[2].body)
        self.assertIn("Your badges are displayed on your profile page. Check it out:", mail.outbox[2].body)

    @override_settings(LOCALE_PATHS=[
        'kitsune/kbadge/tests/test_locale/',
    ])
    def test_notification_l10n(self):
        from kitsune.kbadge import badges  # noqa

        # Localization for this badge's strings is in
        # kitsune/kbadge/tests/test_locale/xx/LC_MESSAGES/django.po
        badge = BadgeFactory(title="Test Badge", description="Test Badge description")

        # Set user preferred language to xx.
        user = UserFactory(profile__locale="xx")

        self.assertEqual(0, len(mail.outbox))

        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description="", badge=badge, user=user)

        self.assertEqual(1, len(mail.outbox))
        self.assertIn("You were awarded the 'Localized Test Badge' badge!", mail.outbox[0].subject)
        self.assertIn("You have been awarded the Localized Test Badge badge!", mail.outbox[0].body)
        self.assertIn("Localized Test Badge description", mail.outbox[0].body)
