from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core import mail
from django.db.models.signals import post_save
from django.test import override_settings

from kitsune.kbadge.utils import get_or_create_badge
from kitsune.questions.badges import QUESTIONS_BADGES
from kitsune.questions.models import QuestionVote, send_vote_update_task
from kitsune.questions.tasks import (
    cleanup_old_spam,
    report_employee_answers,
    update_question_vote_chunk,
)
from kitsune.questions.tests import AnswerFactory, QuestionFactory, QuestionVoteFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class QuestionVoteTestCase(TestCase):
    def setUp(self):
        post_save.disconnect(send_vote_update_task, sender=QuestionVote)

    def tearDown(self):
        post_save.connect(send_vote_update_task, sender=QuestionVote)

    def test_update_question_vote_chunk(self):
        """Test the "update_question_vote_chunk" task."""
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        q3 = QuestionFactory()
        QuestionVoteFactory(question=q1, created=datetime.now() - timedelta(days=1))
        QuestionVoteFactory(question=q1, created=datetime.now() - timedelta(days=2))
        QuestionVoteFactory(question=q1, created=datetime.now() - timedelta(days=9))
        QuestionVoteFactory(question=q2, created=datetime.now() - timedelta(days=3))
        QuestionVoteFactory(question=q2, created=datetime.now() - timedelta(days=6))
        QuestionVoteFactory(question=q2, created=datetime.now() - timedelta(days=7))
        QuestionVoteFactory(question=q2, created=datetime.now() - timedelta(days=8))
        q1.refresh_from_db()
        q2.refresh_from_db()
        q3.refresh_from_db()
        self.assertEqual(q1.num_votes_past_week, 0)
        self.assertEqual(q2.num_votes_past_week, 0)
        self.assertEqual(q3.num_votes_past_week, 0)

        # Actually test the task.
        update_question_vote_chunk([q1.id, q2.id, q3.id])
        q1.refresh_from_db()
        q2.refresh_from_db()
        q3.refresh_from_db()
        self.assertEqual(q1.num_votes_past_week, 2)
        self.assertEqual(q2.num_votes_past_week, 3)
        self.assertEqual(q3.num_votes_past_week, 0)


class SpamCleanupTaskTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @patch("kitsune.questions.handlers.OldSpamCleanupHandler.cleanup_old_spam")
    def test_cleanup_old_spam_task_calls_handler(self, mock_cleanup):
        cleanup_old_spam()
        mock_cleanup.assert_called_once()

    @patch("kitsune.questions.tasks.log")
    def test_cleanup_old_spam_task_logging(self, mock_log):
        cleanup_old_spam()
        # Check that info logging was called
        self.assertTrue(mock_log.info.called)
        # Should have start and completion log messages
        self.assertEqual(mock_log.info.call_count, 2)


class TestMaybeAwardBadge(TestCase):
    @override_settings(BADGE_LIMIT_SUPPORT_FORUM=4)
    def test_maybe_award_badge_for_kb(self):
        badge = get_or_create_badge(
            QUESTIONS_BADGES["answer-badge"],
            year=datetime.now().year,
        )

        a1 = AnswerFactory()
        self.assertFalse(badge.is_awarded_to(a1.creator))

        a2 = AnswerFactory(creator=a1.creator)
        self.assertFalse(badge.is_awarded_to(a1.creator))

        a3 = AnswerFactory(creator=a1.creator)
        self.assertFalse(badge.is_awarded_to(a1.creator))

        a2.delete()
        a3.delete()

        AnswerFactory(creator=a1.creator)
        self.assertTrue(badge.is_awarded_to(a1.creator))


class TestReportEmployeeAnswers(TestCase):
    def test_report_employee_answers(self):
        # Note: This depends on two groups that are created in migrations.
        # If we fix the tests to not run migrations, we'll need to create the
        # two groups here: 'Support Forum Tracked', 'Support Forum Metrics'

        tracked_group, _ = Group.objects.get_or_create(name="Support Forum Tracked")
        tracked_user = UserFactory()
        tracked_user.groups.add(tracked_group)

        report_group, _ = Group.objects.get_or_create(name="Support Forum Metrics")
        report_user = UserFactory()
        report_user.groups.add(report_group)

        # An unanswered question that should get reported
        QuestionFactory(created=datetime.now() - timedelta(days=2))

        # An answered question that should get reported
        q = QuestionFactory(created=datetime.now() - timedelta(days=2))
        AnswerFactory(question=q)

        # A question answered by a tracked user that should get reported
        q = QuestionFactory(created=datetime.now() - timedelta(days=2))
        AnswerFactory(creator=tracked_user, question=q)

        # More questions that shouldn't get reported
        q = QuestionFactory(created=datetime.now() - timedelta(days=3))
        AnswerFactory(creator=tracked_user, question=q)
        q = QuestionFactory(created=datetime.now() - timedelta(days=1))
        AnswerFactory(question=q)
        QuestionFactory()

        report_employee_answers()

        # Get the last email and verify contents
        email = mail.outbox[len(mail.outbox) - 1]

        assert "Number of questions asked: 3" in email.body
        assert "Number of questions answered: 2" in email.body
        assert "{username}: 1".format(username=tracked_user.username) in email.body

        self.assertEqual([report_user.email], email.to)
