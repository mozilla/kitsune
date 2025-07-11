from datetime import datetime, timedelta
from unittest.mock import patch

from django.db.models.signals import post_save

from kitsune.questions.models import QuestionVote, send_vote_update_task
from kitsune.questions.tasks import cleanup_old_spam, update_question_vote_chunk
from kitsune.questions.tests import QuestionFactory, QuestionVoteFactory
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
