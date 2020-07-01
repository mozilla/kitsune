from django.db.models.signals import post_save
from nose.tools import eq_

from kitsune.questions.models import Question
from kitsune.questions.models import QuestionVote
from kitsune.questions.models import send_vote_update_task
from kitsune.questions.tasks import update_question_vote_chunk
from kitsune.questions.tests import QuestionFactory
from kitsune.questions.tests import QuestionVoteFactory
from kitsune.sumo.tests import TestCase


class QuestionVoteTestCase(TestCase):
    def setUp(self):
        post_save.disconnect(send_vote_update_task, sender=QuestionVote)

    def tearDown(self):
        post_save.connect(send_vote_update_task, sender=QuestionVote)

    def test_update_question_vote_chunk(self):
        # Reset the num_votes_past_week counts, I suspect the data gets
        # loaded before I disconnect the signal and they get zeroed out.
        q1 = QuestionFactory()
        QuestionVoteFactory(question=q1)
        q1.num_votes_past_week = 1
        q1.save()

        q2 = QuestionFactory()

        # Actually test the task.
        qs = Question.objects.all().order_by("-num_votes_past_week")
        eq_(q1.pk, qs[0].pk)

        QuestionVoteFactory(question=q2)
        QuestionVoteFactory(question=q2)
        qs = Question.objects.all().order_by("-num_votes_past_week")
        eq_(q1.pk, qs[0].pk)

        update_question_vote_chunk([q.pk for q in qs])
        qs = Question.objects.all().order_by("-num_votes_past_week")
        eq_(q2.pk, qs[0].pk)
