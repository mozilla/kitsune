import elasticutils

from nose.tools import eq_

from sumo.tests import ElasticTestCase

from questions.models import Question, QuestionVote
from questions.tests import TestCaseBase, question, questionvote
from questions.cron import update_weekly_votes


class TestVotes(TestCaseBase):
    """Test QuestionVote counting and cron job."""

    def test_vote_updates_count(self):
        q = Question.objects.all()[0]
        eq_(0, q.num_votes_past_week)

        vote = QuestionVote(question=q, anonymous_id='abc123')
        vote.save()
        eq_(1, q.num_votes_past_week)

    def test_cron_updates_counts(self):
        q = Question.objects.all()[0]
        eq_(0, q.num_votes_past_week)

        vote = QuestionVote(question=q, anonymous_id='abc123')
        vote.save()
        q.num_votes_past_week = 0
        q.save()

        update_weekly_votes()

        q = Question.objects.get(pk=q.pk)
        eq_(1, q.num_votes_past_week)


class TestVotesWithElasticSearch(ElasticTestCase):
    def test_cron_updates_counts(self):
        q = question(save=True)
        self.refresh()

        eq_(q.num_votes_past_week, 0)
        # NB: Need to call .values_dict() here and later otherwise we
        # get a Question object which has data from the database and
        # not the index.
        document = (elasticutils.S(Question)
                                .values_dict('num_votes_past_week')
                                .query(id=q.id))[0]
        eq_(document['num_votes_past_week'], 0)

        vote = questionvote(question=q, anonymous_id='abc123')
        vote.save()
        q.num_votes_past_week = 0
        q.save()

        update_weekly_votes()

        q = Question.objects.get(pk=q.pk)
        eq_(1, q.num_votes_past_week)

        document = (elasticutils.S(Question)
                                .values_dict('num_votes_past_week')
                                .query(id=q.id))[0]
        eq_(document['num_votes_past_week'], 1)
