from django.contrib.auth.models import User
from django.db.models.signals import post_save

from nose.tools import eq_

from kitsune.questions.models import (
    Question, QuestionVote, send_vote_update_task, Answer)
from kitsune.questions.tasks import update_question_vote_chunk
from kitsune.questions.tests import question, questionvote
from kitsune.sumo.tests import TestCase


class QuestionVoteTestCase(TestCase):

    def setUp(self):
        post_save.disconnect(send_vote_update_task, sender=QuestionVote)

    def tearDown(self):
        post_save.connect(send_vote_update_task, sender=QuestionVote)

    def test_update_question_vote_chunk(self):
        # Reset the num_votes_past_week counts, I suspect the data gets
        # loaded before I disconnect the signal and they get zeroed out.
        q1 = question(save=True)
        questionvote(question=q1, save=True)
        q1.num_votes_past_week = 1
        q1.save()

        q2 = question(save=True)

        # Actually test the task.
        qs = Question.objects.all().order_by('-num_votes_past_week')
        eq_(q1.pk, qs[0].pk)

        questionvote(question=q2, save=True)
        questionvote(question=q2, save=True)
        qs = Question.uncached.all().order_by('-num_votes_past_week')
        eq_(q1.pk, qs[0].pk)

        update_question_vote_chunk([q.pk for q in qs])
        qs = Question.uncached.all().order_by('-num_votes_past_week')
        eq_(q2.pk, qs[0].pk)
