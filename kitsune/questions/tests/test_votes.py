from django.core.management import call_command
from nose.tools import eq_

from kitsune.questions.models import Question
from kitsune.questions.models import QuestionMappingType
from kitsune.questions.tests import QuestionFactory
from kitsune.questions.tests import QuestionVoteFactory
from kitsune.questions.tests import TestCaseBase
from kitsune.search.tests.test_es import ElasticTestCase


class TestVotes(TestCaseBase):
    """Test QuestionVote counting and cron job."""

    def test_vote_updates_count(self):
        q = QuestionFactory()
        eq_(0, q.num_votes_past_week)

        QuestionVoteFactory(question=q, anonymous_id='abc123')

        q = Question.objects.get(id=q.id)
        eq_(1, q.num_votes_past_week)

    def test_cron_updates_counts(self):
        q = QuestionFactory()
        eq_(0, q.num_votes_past_week)

        QuestionVoteFactory(question=q, anonymous_id='abc123')

        q.num_votes_past_week = 0
        q.save()

        call_command('update_weekly_votes')

        q = Question.objects.get(pk=q.pk)
        eq_(1, q.num_votes_past_week)


class TestVotesWithElasticSearch(ElasticTestCase):
    def test_cron_updates_counts(self):
        q = QuestionFactory()
        self.refresh()

        eq_(q.num_votes_past_week, 0)
        # NB: Need to call .values_dict() here and later otherwise we
        # get a Question object which has data from the database and
        # not the index.
        document = (QuestionMappingType.search()
                    .filter(id=q.id))[0]

        eq_(document['question_num_votes_past_week'], 0)

        QuestionVoteFactory(question=q, anonymous_id='abc123')
        q.num_votes_past_week = 0
        q.save()

        call_command('update_weekly_votes')
        self.refresh()

        q = Question.objects.get(pk=q.pk)
        eq_(1, q.num_votes_past_week)

        document = (QuestionMappingType.search()
                    .filter(id=q.id))[0]

        eq_(document['question_num_votes_past_week'], 1)
