from nose.tools import eq_

from kitsune.questions.models import Question, Answer
from kitsune.questions.tests import QuestionFactory, AnswerFactory
from kitsune.questions.utils import (
    num_questions,
    num_answers,
    num_solutions,
    mark_content_as_spam,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class ContributionCountTestCase(TestCase):
    def test_num_questions(self):
        """Answers are counted correctly on a user."""
        u = UserFactory()
        eq_(num_questions(u), 0)

        q1 = QuestionFactory(creator=u)
        eq_(num_questions(u), 1)

        q2 = QuestionFactory(creator=u)
        eq_(num_questions(u), 2)

        q1.delete()
        eq_(num_questions(u), 1)

        q2.delete()
        eq_(num_questions(u), 0)

    def test_num_answers(self):
        u = UserFactory()
        q = QuestionFactory()
        eq_(num_answers(u), 0)

        a1 = AnswerFactory(creator=u, question=q)
        eq_(num_answers(u), 1)

        a2 = AnswerFactory(creator=u, question=q)
        eq_(num_answers(u), 2)

        a1.delete()
        eq_(num_answers(u), 1)

        a2.delete()
        eq_(num_answers(u), 0)

    def test_num_solutions(self):
        u = UserFactory()
        q1 = QuestionFactory()
        q2 = QuestionFactory()
        a1 = AnswerFactory(creator=u, question=q1)
        a2 = AnswerFactory(creator=u, question=q2)
        eq_(num_solutions(u), 0)

        q1.solution = a1
        q1.save()
        eq_(num_solutions(u), 1)

        q2.solution = a2
        q2.save()
        eq_(num_solutions(u), 2)

        q1.solution = None
        q1.save()
        eq_(num_solutions(u), 1)

        a2.delete()
        eq_(num_solutions(u), 0)


class FlagUserContentAsSpamTestCase(TestCase):
    def test_flag_content_as_spam(self):
        # Create some questions and answers by the user.
        u = UserFactory()
        QuestionFactory(creator=u)
        QuestionFactory(creator=u)
        AnswerFactory(creator=u)
        AnswerFactory(creator=u)
        AnswerFactory(creator=u)

        # Verify they are not marked as spam yet.
        eq_(2, Question.objects.filter(is_spam=False, creator=u).count())
        eq_(0, Question.objects.filter(is_spam=True, creator=u).count())
        eq_(3, Answer.objects.filter(is_spam=False, creator=u).count())
        eq_(0, Answer.objects.filter(is_spam=True, creator=u).count())

        # Flag content as spam and verify it is updated.
        mark_content_as_spam(u, UserFactory())
        eq_(0, Question.objects.filter(is_spam=False, creator=u).count())
        eq_(2, Question.objects.filter(is_spam=True, creator=u).count())
        eq_(0, Answer.objects.filter(is_spam=False, creator=u).count())
        eq_(3, Answer.objects.filter(is_spam=True, creator=u).count())
