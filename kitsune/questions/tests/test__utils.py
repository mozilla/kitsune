from nose.tools import eq_

from kitsune.questions.models import Question, Answer
from kitsune.questions.tests import question, answer
from kitsune.questions.utils import (
    num_questions, num_answers, num_solutions, mark_content_as_spam)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import user


class ContributionCountTestCase(TestCase):
    def test_num_questions(self):
        """Answers are counted correctly on a user."""
        u = user(save=True)
        eq_(num_questions(u), 0)

        q1 = question(creator=u, save=True)
        eq_(num_questions(u), 1)

        q2 = question(creator=u, save=True)
        eq_(num_questions(u), 2)

        q1.delete()
        eq_(num_questions(u), 1)

        q2.delete()
        eq_(num_questions(u), 0)

    def test_num_answers(self):
        u = user(save=True)
        q = question(save=True)
        eq_(num_answers(u), 0)

        a1 = answer(creator=u, question=q, save=True)
        eq_(num_answers(u), 1)

        a2 = answer(creator=u, question=q, save=True)
        eq_(num_answers(u), 2)

        a1.delete()
        eq_(num_answers(u), 1)

        a2.delete()
        eq_(num_answers(u), 0)

    def test_num_solutions(self):
        u = user(save=True)
        q1 = question(save=True)
        q2 = question(save=True)
        a1 = answer(creator=u, question=q1, save=True)
        a2 = answer(creator=u, question=q2, save=True)
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
        u = user(save=True)
        question(creator=u, save=True)
        question(creator=u, save=True)
        answer(creator=u, save=True)
        answer(creator=u, save=True)
        answer(creator=u, save=True)

        # Verify they are not marked as spam yet.
        eq_(2, Question.objects.filter(is_spam=False, creator=u).count())
        eq_(0, Question.objects.filter(is_spam=True, creator=u).count())
        eq_(3, Answer.objects.filter(is_spam=False, creator=u).count())
        eq_(0, Answer.objects.filter(is_spam=True, creator=u).count())

        # Flag content as spam and verify it is updated.
        mark_content_as_spam(u, user(save=True))
        eq_(0, Question.objects.filter(is_spam=False, creator=u).count())
        eq_(2, Question.objects.filter(is_spam=True, creator=u).count())
        eq_(0, Answer.objects.filter(is_spam=False, creator=u).count())
        eq_(3, Answer.objects.filter(is_spam=True, creator=u).count())
