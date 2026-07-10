from django.core import mail
from django.test import override_settings

from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.templatetags.jinja_helpers import display_name
from kitsune.users.tests import UserFactory

TEST_BADGE_TITLE = "Test Badge"
LOCALIZED_TEST_BADGE_TITLE = "Localized Test Badge"  # see ./test_locale/xx/LC_MESSAGES/django.po > ./test_locale/xx/LC_MESSAGES/django.mo
TEST_BADGE_DESCRIPTION = "Test Badge description"
LOCALIZED_TEST_BADGE_DESCRIPTION = "Localized Test Badge description"  # see ./test_locale/xx/LC_MESSAGES/django.po > ./test_locale/xx/LC_MESSAGES/django.mo
TEST_AWARD_DESCRIPTION = "Award description"
EMAIL_SUBJECT = "You were awarded the '{badge_title}' badge!"
EMAIL_BODY_CONGRADULATIONS = "Congratulations!"
EMAIL_BODY_INTRO_NO_AWARDER = "You have been awarded the {badge_title} badge!"
EMAIL_BODY_INTRO_AWARDER = "{awarder_name} has awarded you the {badge_title} badge!"
EMAIL_BODY_THANK_YOU = "Mozilla Support is made possible by volunteers like you. "
"Thank you for the time, knowledge, and care you've shared with the community."
EMAIL_BODY_PROFILE_PAGE = "Your badges are displayed on your profile page. Check it out:"


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
            AwardFactory(description=TEST_AWARD_DESCRIPTION, badge=new_badge)

        self.assertEqual(1, len(mail.outbox))

    def test_notification_contents(self):
        from kitsune.kbadge import badges  # noqa

        badge = BadgeFactory(title=TEST_BADGE_TITLE, description=TEST_BADGE_DESCRIPTION)

        # Check the mail queue first.
        self.assertEqual(0, len(mail.outbox))

        # Create an award without description.
        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description="", badge=badge)

        self.assertEqual(1, len(mail.outbox))
        self.assertIn(EMAIL_SUBJECT.format(badge_title=TEST_BADGE_TITLE), mail.outbox[0].subject)
        self.assertIn(EMAIL_BODY_CONGRADULATIONS, mail.outbox[0].body)
        self.assertIn(EMAIL_BODY_INTRO_NO_AWARDER.format(badge_title=TEST_BADGE_TITLE), mail.outbox[0].body)
        # The email should include the badge description in such case.
        self.assertIn(TEST_BADGE_DESCRIPTION, mail.outbox[0].body)
        self.assertIn(EMAIL_BODY_THANK_YOU, mail.outbox[0].body)
        self.assertIn(EMAIL_BODY_PROFILE_PAGE, mail.outbox[0].body)

        # Create an award with description.
        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description=TEST_AWARD_DESCRIPTION, badge=badge)

        self.assertEqual(2, len(mail.outbox))
        self.assertIn(EMAIL_SUBJECT.format(badge_title=TEST_BADGE_TITLE), mail.outbox[1].subject)
        self.assertIn(EMAIL_BODY_CONGRADULATIONS, mail.outbox[1].body)
        self.assertIn(EMAIL_BODY_INTRO_NO_AWARDER.format(badge_title=TEST_BADGE_TITLE), mail.outbox[1].body)
        # The email should include the award description in such case.
        self.assertIn(TEST_AWARD_DESCRIPTION, mail.outbox[1].body)
        # The email should NOT include the badge description in such case.
        self.assertNotIn(TEST_BADGE_DESCRIPTION, mail.outbox[1].body)
        self.assertIn(EMAIL_BODY_THANK_YOU, mail.outbox[1].body)
        self.assertIn(EMAIL_BODY_PROFILE_PAGE, mail.outbox[1].body)

        # Create an award with description and awarder.
        awarder = UserFactory()
        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description=TEST_AWARD_DESCRIPTION, creator=awarder, badge=badge)

        self.assertEqual(3, len(mail.outbox))
        self.assertIn(EMAIL_SUBJECT.format(badge_title=TEST_BADGE_TITLE), mail.outbox[2].subject)
        self.assertIn(EMAIL_BODY_CONGRADULATIONS, mail.outbox[2].body)
        # The email should mention the awarder in such case.
        self.assertIn(EMAIL_BODY_INTRO_AWARDER.format(awarder_name=display_name(awarder), badge_title=TEST_BADGE_TITLE), mail.outbox[2].body)
        # The generic award message should NOT appear.
        self.assertNotIn(EMAIL_BODY_INTRO_NO_AWARDER.format(badge_title=TEST_BADGE_TITLE), mail.outbox[2].body)
        # The email should include the award description in such case.
        self.assertIn(TEST_AWARD_DESCRIPTION, mail.outbox[2].body)
        # The email should NOT include the badge description in such case.
        self.assertNotIn(TEST_BADGE_DESCRIPTION, mail.outbox[2].body)
        self.assertIn(EMAIL_BODY_THANK_YOU, mail.outbox[2].body)
        self.assertIn(EMAIL_BODY_PROFILE_PAGE, mail.outbox[2].body)

    @override_settings(LOCALE_PATHS=[
        'kitsune/kbadge/tests/test_locale/',
    ])
    def test_notification_l10n(self):
        from kitsune.kbadge import badges  # noqa

        # Localization for this badge's strings is in
        # kitsune/kbadge/tests/test_locale/xx/LC_MESSAGES/django.po
        badge = BadgeFactory(title=TEST_BADGE_TITLE, description=TEST_BADGE_DESCRIPTION)

        # Set user preferred language to xx.
        user = UserFactory(profile__locale="xx")

        self.assertEqual(0, len(mail.outbox))

        with self.captureOnCommitCallbacks(execute=True):
            AwardFactory(description="", badge=badge, user=user)

        self.assertEqual(1, len(mail.outbox))
        self.assertIn(EMAIL_SUBJECT.format(badge_title=LOCALIZED_TEST_BADGE_TITLE), mail.outbox[0].subject)
        self.assertIn(EMAIL_BODY_INTRO_NO_AWARDER.format(badge_title=LOCALIZED_TEST_BADGE_TITLE), mail.outbox[0].body)
        self.assertIn(LOCALIZED_TEST_BADGE_DESCRIPTION, mail.outbox[0].body)
