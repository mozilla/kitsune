import mock

from kitsune.questions.karma_actions import (
    AnswerAction, AnswerMarkedHelpfulAction, AnswerMarkedNotHelpfulAction,
    FirstAnswerAction, SolutionAction)
from kitsune.questions.tests import TestCaseBase, answer
from kitsune.sumo.tests import post
from kitsune.users.tests import user


class KarmaTests(TestCaseBase):
    """Tests for karma actions."""
    def setUp(self):
        super(KarmaTests, self).setUp()
        self.user = user(save=True)

    @mock.patch.object(AnswerAction, 'save')
    def test_new_answer(self, answer):
        answer(save=True)
        assert answer.called

    @mock.patch.object(FirstAnswerAction, 'save')
    def test_first_answer(self, first):
        answer(save=True)
        assert first.called

    @mock.patch.object(SolutionAction, 'save')
    def test_solution(self, save):
        a = answer(save=True)
        q = a.question

        self.client.login(username=q.creator.username, password='testpass')
        post(self.client, 'questions.solve', args=[q.id, a.id])
        assert save.called

    @mock.patch.object(SolutionAction, 'delete')
    def test_unsolve(self, delete):
        a = answer(save=True)
        q = a.question

        self.client.login(username=q.creator.username, password='testpass')
        q.solution = a
        q.save()
        post(self.client, 'questions.unsolve', args=[q.id, a.id])
        assert delete.called

    @mock.patch.object(AnswerAction, 'delete')
    def test_delete_answer(self, delete):
        a = answer(save=True)
        a.delete()
        assert delete.called

    @mock.patch.object(SolutionAction, 'delete')
    @mock.patch.object(AnswerAction, 'delete')
    def test_delete_solution(self, a_delete, s_delete):
        a = answer(save=True)
        q = a.question
        q.solution = a
        q.save()
        a.delete()
        assert a_delete.called
        assert s_delete.called

    @mock.patch.object(AnswerMarkedHelpfulAction, 'save')
    def test_helpful_vote(self, save):
        a = answer(save=True)
        q = a.question
        post(self.client, 'questions.answer_vote', {'helpful': True},
             args=[q.id, a.id])
        assert save.called

    @mock.patch.object(AnswerMarkedNotHelpfulAction, 'save')
    def test_nothelpful_vote(self, save):
        a = answer(save=True)
        q = a.question
        post(self.client, 'questions.answer_vote', {'not-helpful': True},
             args=[q.id, a.id])
        assert save.called
