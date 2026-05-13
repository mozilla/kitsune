from django.contrib.contenttypes.models import ContentType

from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.tests import TestCaseBase
from kitsune.questions.models import Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import get, post
from kitsune.users.tests import UserFactory, add_permission


class FlagTestCase(TestCaseBase):
    """Test the flag view."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.question = QuestionFactory(creator=self.user)

        self.client.login(username=self.user.username, password="testpass")

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    def test_flag(self):
        """Flag a question."""
        d = {
            "content_type": ContentType.objects.get_for_model(Question).id,
            "object_id": self.question.id,
            "reason": "spam",
            "next": self.question.get_absolute_url(),
        }
        post(self.client, "flagit.flag", d)
        self.assertEqual(1, FlaggedObject.objects.count())

        flag = FlaggedObject.objects.all()[0]
        self.assertEqual(self.user.username, flag.creator.username)
        self.assertEqual("spam", flag.reason)
        self.assertEqual(self.question, flag.content_object)


class SpamFlagReconciliationTestCase(TestCaseBase):
    """Moderator decisions on an Answer's spam flag propagate to the Answer.

    Rejection unmarks-as-spam (see mozilla/sumo#2948); acceptance
    backfills marked_as_spam when missing so the cleanup cron can
    eventually purge auto-flagged answers.
    """

    def setUp(self):
        super().setUp()
        self.moderator = UserFactory()
        add_permission(self.moderator, FlaggedObject, "can_moderate")
        self.flagger = UserFactory()
        self.client.login(username=self.moderator.username, password="testpass")

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    def _flag(self, obj, reason=FlaggedObject.REASON_SPAM):
        return FlaggedObject.objects.create(
            content_object=obj,
            reason=reason,
            status=FlaggedObject.FLAG_PENDING,
            creator=self.flagger,
        )

    def _reject(self, flag):
        return post(
            self.client,
            "flagit.update",
            {"status": FlaggedObject.FLAG_REJECTED},
            args=[flag.id],
        )

    def _accept(self, flag):
        return post(
            self.client,
            "flagit.update",
            {"status": FlaggedObject.FLAG_ACCEPTED},
            args=[flag.id],
        )

    def test_rejecting_spam_flag_clears_is_spam_on_answer(self):
        answer = AnswerFactory()
        answer.is_spam = True
        answer.save()
        flag = self._flag(answer)

        self._reject(flag)

        answer.refresh_from_db()
        self.assertFalse(answer.is_spam)
        self.assertIsNone(answer.marked_as_spam)
        self.assertIsNone(answer.marked_as_spam_by)

    def test_mark_as_spam_sticks_after_earlier_rejection(self):
        """Regression for mozilla/sumo#2948.

        Auto-flag -> moderator rejects the flag -> moderator later clicks
        Mark as spam. The manual mark must persist across subsequent page
        renders of the question-detail view.
        """
        answer = AnswerFactory()
        answer.is_spam = True
        answer.save()
        flag = self._flag(answer)

        self._reject(flag)

        post(self.client, "questions.mark_spam", {"answer_id": answer.id})

        get(self.client, "questions.details", kwargs={"question_id": answer.question_id})

        answer.refresh_from_db()
        self.assertTrue(answer.is_spam)
        self.assertEqual(self.moderator, answer.marked_as_spam_by)

    def test_rejecting_non_spam_flag_leaves_is_spam_alone(self):
        answer = AnswerFactory()
        answer.is_spam = True
        answer.save()
        flag = self._flag(answer, reason=FlaggedObject.REASON_ABUSE)

        self._reject(flag)

        answer.refresh_from_db()
        self.assertTrue(answer.is_spam)

    def test_rejection_overrides_prior_manual_mark_as_spam(self):
        other_moderator = UserFactory()
        answer = AnswerFactory()
        answer.mark_as_spam(other_moderator)
        self.assertTrue(answer.is_spam)
        self.assertEqual(other_moderator, answer.marked_as_spam_by)

        flag = self._flag(answer)
        self._reject(flag)

        answer.refresh_from_db()
        self.assertFalse(answer.is_spam)
        self.assertIsNone(answer.marked_as_spam)
        self.assertIsNone(answer.marked_as_spam_by)

    def test_rejecting_spam_flag_on_non_aaq_content_is_noop(self):
        """Content types without is_spam (e.g. user profiles) are unaffected."""
        target = UserFactory()
        flag = self._flag(target.profile)

        response = self._reject(flag)

        self.assertIn(response.status_code, (200, 302))
        flag.refresh_from_db()
        self.assertEqual(FlaggedObject.FLAG_REJECTED, flag.status)

    def test_accepting_spam_flag_backfills_marked_as_spam(self):
        """Acceptance backfills audit metadata on an auto-flagged answer."""
        answer = AnswerFactory()
        answer.is_spam = True
        answer.save()
        flag = self._flag(answer)

        self._accept(flag)

        answer.refresh_from_db()
        self.assertTrue(answer.is_spam)
        self.assertIsNotNone(answer.marked_as_spam)
        self.assertEqual(self.moderator, answer.marked_as_spam_by)

    def test_accepting_spam_flag_preserves_existing_manual_mark(self):
        """Acceptance does not overwrite an answer already manually marked."""
        other_moderator = UserFactory()
        answer = AnswerFactory()
        answer.mark_as_spam(other_moderator)
        original_timestamp = answer.marked_as_spam

        flag = self._flag(answer)
        self._accept(flag)

        answer.refresh_from_db()
        self.assertTrue(answer.is_spam)
        self.assertEqual(original_timestamp, answer.marked_as_spam)
        self.assertEqual(other_moderator, answer.marked_as_spam_by)

    def test_accepting_non_spam_flag_does_not_touch_answer(self):
        """Accepting e.g. an abuse flag leaves the Answer untouched."""
        answer = AnswerFactory()
        answer.is_spam = True
        answer.save()
        flag = self._flag(answer, reason=FlaggedObject.REASON_ABUSE)

        self._accept(flag)

        answer.refresh_from_db()
        self.assertTrue(answer.is_spam)
        self.assertIsNone(answer.marked_as_spam)
        self.assertIsNone(answer.marked_as_spam_by)

    def test_accepting_spam_flag_on_non_spam_answer_is_noop(self):
        """Acceptance on is_spam=False content does not retroactively mark."""
        answer = AnswerFactory()  # is_spam defaults to False
        flag = self._flag(answer)

        self._accept(flag)

        answer.refresh_from_db()
        self.assertFalse(answer.is_spam)
        self.assertIsNone(answer.marked_as_spam)
        self.assertIsNone(answer.marked_as_spam_by)


class ModerationFlagSupersedeTestCase(TestCaseBase):
    """Only principals with flagit.can_moderate may supersede a pending
    CONTENT_MODERATION flag by submitting a different-reason flag on the
    same object. See SUMO-009."""

    def setUp(self):
        super().setUp()
        self.flagger = UserFactory()
        self.bot = UserFactory()
        self.question = QuestionFactory()
        self.moderation_flag = FlaggedObject.objects.create(
            content_object=self.question,
            reason=FlaggedObject.REASON_CONTENT_MODERATION,
            status=FlaggedObject.FLAG_PENDING,
            creator=self.bot,
            notes="LLM topic classification fixture",
        )

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    def _post_flag(self, reason):
        return post(
            self.client,
            "flagit.flag",
            {
                "content_type": ContentType.objects.get_for_model(Question).id,
                "object_id": self.question.id,
                "reason": reason,
            },
        )

    def test_regular_user_spam_flag_does_not_touch_moderation_flag(self):
        """A non-moderator submitting a spam flag must leave an existing
        pending CONTENT_MODERATION flag unchanged."""
        self.client.login(username=self.flagger.username, password="testpass")

        self._post_flag(FlaggedObject.REASON_SPAM)

        self.moderation_flag.refresh_from_db()
        self.assertEqual(self.moderation_flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(self.moderation_flag.reason, FlaggedObject.REASON_CONTENT_MODERATION)

    def test_moderator_spam_flag_supersedes_moderation_flag_as_duplicate(self):
        """A moderator submitting a spam flag soft-deletes the pending
        CONTENT_MODERATION flag by marking it FLAG_DUPLICATE rather than
        destroying the row."""
        moderator = UserFactory()
        add_permission(moderator, FlaggedObject, "can_moderate")
        self.client.login(username=moderator.username, password="testpass")

        self._post_flag(FlaggedObject.REASON_SPAM)

        self.moderation_flag.refresh_from_db()
        self.assertEqual(self.moderation_flag.status, FlaggedObject.FLAG_DUPLICATE)
        self.assertEqual(self.moderation_flag.reason, FlaggedObject.REASON_CONTENT_MODERATION)
        self.assertEqual(self.moderation_flag.notes, "LLM topic classification fixture")

    def test_user_moderation_flag_marks_new_flag_duplicate(self):
        """Regression guard: when the new flag's reason is CONTENT_MODERATION,
        the existing pending moderation flag stays pending and the new flag
        is recorded as FLAG_DUPLICATE."""
        self.client.login(username=self.flagger.username, password="testpass")

        self._post_flag(FlaggedObject.REASON_CONTENT_MODERATION)

        self.moderation_flag.refresh_from_db()
        self.assertEqual(self.moderation_flag.status, FlaggedObject.FLAG_PENDING)
        new_flag = FlaggedObject.objects.get(creator=self.flagger)
        self.assertEqual(new_flag.status, FlaggedObject.FLAG_DUPLICATE)
        self.assertEqual(new_flag.reason, FlaggedObject.REASON_CONTENT_MODERATION)
