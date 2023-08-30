from datetime import datetime, timedelta

from django.db.models.signals import post_save

from kitsune.questions.models import QuestionVote, send_vote_update_task
from kitsune.questions.tasks import update_question_vote_chunk
from kitsune.questions.tests import QuestionFactory, QuestionVoteFactory
from kitsune.sumo.tests import TestCase


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
