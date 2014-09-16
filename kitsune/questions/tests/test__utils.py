from nose.tools import eq_

from kitsune.questions.tests import question, answer
from kitsune.questions.utils import num_questions, num_answers, num_solutions
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.tests import user


class ContributionCountTestCase(ElasticTestCase):
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
        self.refresh()
        eq_(num_answers(u), 0)

        a1 = answer(creator=u, question=q, save=True)
        self.refresh()
        eq_(num_answers(u), 1)

        a2 = answer(creator=u, question=q, save=True)
        self.refresh()
        eq_(num_answers(u), 2)

        a1.delete()
        self.refresh()
        eq_(num_answers(u), 1)

        a2.delete()
        self.refresh()
        eq_(num_answers(u), 0)

    def test_num_solutions(self):
        u = user(save=True)
        q1 = question(save=True)
        q2 = question(save=True)
        a1 = answer(creator=u, question=q1, save=True)
        a2 = answer(creator=u, question=q2, save=True)
        self.refresh()
        eq_(num_solutions(u), 0)

        q1.solution = a1
        q1.save()
        self.refresh()
        eq_(num_solutions(u), 1)

        q2.solution = a2
        q2.save()
        self.refresh()
        eq_(num_solutions(u), 2)

        q1.solution = None
        q1.save()
        self.refresh()
        eq_(num_solutions(u), 1)

        a2.delete()
        self.refresh()
        eq_(num_solutions(u), 0)
