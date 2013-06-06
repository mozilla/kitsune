import mock

from kitsune.questions.karma_actions import (
    AnswerAction, AnswerMarkedHelpfulAction, AnswerMarkedNotHelpfulAction,
    FirstAnswerAction, SolutionAction)
from kitsune.questions.models import Question, Answer
from kitsune.questions.tests import TestCaseBase
from kitsune.sumo.tests import post
from kitsune.users.tests import user


class KarmaTests(TestCaseBase):
    """Tests for karma actions."""
    def setUp(self):
        super(KarmaTests, self).setUp()
        self.user = user(save=True)

    @mock.patch.object(AnswerAction, 'save')
    @mock.patch.object(FirstAnswerAction, 'save')
    def test_new_answer(self, first, answer):
        question = Question.objects.all()[0]
        Answer.objects.create(question=question, creator=self.user)
        assert answer.called
        assert not first.called

    @mock.patch.object(AnswerAction, 'save')
    @mock.patch.object(FirstAnswerAction, 'save')
    def test_first_answer(self, first, answer):
        question = Question.objects.all()[1]
        Answer.objects.create(question=question, creator=self.user)
        assert answer.called
        assert first.called

    @mock.patch.object(SolutionAction, 'save')
    def test_solution(self, save):
        answer = Answer.objects.get(pk=1)
        question = answer.question
        self.client.login(username='jsocol', password='testpass')
        post(self.client, 'questions.solve', args=[question.id, answer.id])
        assert save.called

    @mock.patch.object(SolutionAction, 'delete')
    def test_unsolve(self, delete):
        answer = Answer.objects.get(pk=1)
        question = answer.question
        self.client.login(username='jsocol', password='testpass')
        question.solution = answer
        question.save()
        post(self.client, 'questions.unsolve', args=[question.id, answer.id])
        assert delete.called

    @mock.patch.object(AnswerAction, 'delete')
    def test_delete_answer(self, delete):
        answer = Answer.objects.get(pk=1)
        answer.delete()
        assert delete.called

    @mock.patch.object(SolutionAction, 'delete')
    @mock.patch.object(AnswerAction, 'delete')
    def test_delete_solution(self, a_delete, s_delete):
        answer = Answer.objects.get(pk=1)
        question = answer.question
        question.solution = answer
        question.save()
        answer.delete()
        assert a_delete.called
        assert s_delete.called

    @mock.patch.object(AnswerMarkedHelpfulAction, 'save')
    def test_helpful_vote(self, save):
        answer = Answer.objects.get(pk=1)
        question = answer.question
        post(self.client, 'questions.answer_vote', {'helpful': True},
             args=[question.id, answer.id])
        assert save.called

    @mock.patch.object(AnswerMarkedNotHelpfulAction, 'save')
    def test_nothelpful_vote(self, save):
        answer = Answer.objects.get(pk=1)
        question = answer.question
        post(self.client, 'questions.answer_vote', {'not-helpful': True},
             args=[question.id, answer.id])
        assert save.called
