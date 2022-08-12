from django.core.management import call_command

from kitsune.questions.models import Question
from kitsune.questions.tests import QuestionFactory, QuestionVoteFactory, TestCaseBase


class TestVotes(TestCaseBase):
    """Test QuestionVote counting and cron job."""

    def test_vote_updates_count(self):
        q = QuestionFactory()
        self.assertEqual(0, q.num_votes_past_week)

        QuestionVoteFactory(question=q, anonymous_id="abc123")

        q = Question.objects.get(id=q.id)
        self.assertEqual(1, q.num_votes_past_week)

    def test_cron_updates_counts(self):
        q = QuestionFactory()
        self.assertEqual(0, q.num_votes_past_week)

        QuestionVoteFactory(question=q, anonymous_id="abc123")

        q.num_votes_past_week = 0
        q.save()

        call_command("update_weekly_votes")

        q = Question.objects.get(pk=q.pk)
        self.assertEqual(1, q.num_votes_past_week)
