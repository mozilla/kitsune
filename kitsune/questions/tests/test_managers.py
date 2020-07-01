from nose.tools import eq_

from kitsune.questions.models import Answer
from kitsune.questions.models import Question
from kitsune.questions.tests import AnswerFactory
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import TestCase


class QuestionManagerTestCase(TestCase):
    def test_done(self):
        """Verify the done queryset."""
        # Create a question, there shouldn't be any done yet.
        q = QuestionFactory()
        eq_(0, Question.objects.done().count())

        # Add an answer, there shouldn't be any done yet.
        a = AnswerFactory(question=q)
        eq_(0, Question.objects.done().count())

        # Make it the solution, there should be one done.
        q.solution = a
        q.save()
        eq_(1, Question.objects.done().count())

        # Create a locked questions, there should be two done.
        QuestionFactory(is_locked=True)
        eq_(2, Question.objects.done().count())

    def test_responded(self):
        """Verify the responded queryset."""
        # Create a question, there shouldn't be any responded yet.
        q = QuestionFactory()
        eq_(0, Question.objects.responded().count())

        # Add an answer, there should be one responded.
        a = AnswerFactory(question=q)
        eq_(1, Question.objects.responded().count())

        # Add an answer by the creator, there should be none responded.
        a = AnswerFactory(creator=q.creator, question=q)
        eq_(0, Question.objects.responded().count())

        # Add another answer, there should be one responded.
        a = AnswerFactory(question=q)
        eq_(1, Question.objects.responded().count())

        # Lock it, there should be none responded.
        q.is_locked = True
        q.save()
        eq_(0, Question.objects.responded().count())

        # Unlock it and mark solved, there should be none responded.
        q.is_locked = False
        q.solution = a
        q.save()
        eq_(0, Question.objects.responded().count())

    def test_needs_attention(self):
        """Verify the needs_attention queryset."""
        # Create a question, there shouldn't be one needs_attention.
        q = QuestionFactory()
        eq_(1, Question.objects.needs_attention().count())

        # Add an answer, there should be no needs_attention.
        a = AnswerFactory(question=q)
        eq_(0, Question.objects.needs_attention().count())

        # Add an answer by the creator, there should be one needs_attention.
        a = AnswerFactory(creator=q.creator, question=q)
        eq_(1, Question.objects.needs_attention().count())

        # Lock it, there should be none responded.
        q.is_locked = True
        q.save()
        eq_(0, Question.objects.needs_attention().count())

        # Unlock it and mark solved, there should be none responded.
        q.is_locked = False
        q.solution = a
        q.save()
        eq_(0, Question.objects.needs_attention().count())

    def test_needs_info(self):
        """Verify the needs_info queryset."""
        q = QuestionFactory()

        # There should be no needs_info questions yet.
        eq_(0, Question.objects.needs_info().count())

        # Tag a question and there should be one needs_info question.
        q.set_needs_info()
        eq_(1, Question.objects.needs_info().count())

        # Remove tag and there shouldn't be any anymore.
        q.unset_needs_info()
        eq_(0, Question.objects.needs_info().count())


class AnswerManagerTestCase(TestCase):
    def test_not_by_asker(self):
        """Verify that only answers by users other than the original asker are returned"""
        q = QuestionFactory()

        # Add an answer by the original asker
        AnswerFactory(question=q, creator=q.creator)
        eq_(0, Answer.objects.not_by_asker().count())

        # Add an answer by someone else
        AnswerFactory(question=q)
        eq_(1, Answer.objects.not_by_asker().count())
