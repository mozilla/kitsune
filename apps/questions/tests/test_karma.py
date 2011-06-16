import mock

from questions.karma_actions import (AnswerAction, AnswerMarkedHelpfulAction,
                                     FirstAnswerAction, SolutionAction)
from questions.models import Question, Answer
from questions.tests import TestCaseBase
from sumo.tests import post
from users.tests import user


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

    @mock.patch.object(AnswerMarkedHelpfulAction, 'save')
    def test_helpful_vote(self, save):
        answer = Answer.objects.get(pk=1)
        question = answer.question
        post(self.client, 'questions.answer_vote', {'helpful': True},
             args=[question.id, answer.id])
        assert save.called
