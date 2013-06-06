from nose.tools import eq_

from kitsune.questions.models import (
    Question, QuestionMappingType, QuestionVote)
from kitsune.questions.tests import TestCaseBase, question, questionvote
from kitsune.questions.cron import update_weekly_votes
from kitsune.search.tests.test_es import ElasticTestCase


class TestVotes(TestCaseBase):
    """Test QuestionVote counting and cron job."""

    def test_vote_updates_count(self):
        q = Question.objects.all()[0]
        eq_(0, q.num_votes_past_week)

        vote = QuestionVote(question=q, anonymous_id='abc123')
        vote.save()

        q = Question.uncached.get(id=q.id)
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
        document = (QuestionMappingType.search()
                    .values_dict('question_num_votes_past_week')
                    .filter(id=q.id))[0]
        eq_(document['question_num_votes_past_week'], 0)

        vote = questionvote(question=q, anonymous_id='abc123')
        vote.save()
        q.num_votes_past_week = 0
        q.save()

        update_weekly_votes()
        self.refresh()

        q = Question.objects.get(pk=q.pk)
        eq_(1, q.num_votes_past_week)

        document = (QuestionMappingType.search()
                    .values_dict('question_num_votes_past_week')
                    .filter(id=q.id))[0]
        eq_(document['question_num_votes_past_week'], 1)
