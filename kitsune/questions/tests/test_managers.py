from nose.tools import eq_

from kitsune.questions import config
from kitsune.questions.models import Question
from kitsune.questions.tests import answer, question
from kitsune.sumo.tests import TestCase
from kitsune.tags.tests import tag


class QuestionManagerTestCase(TestCase):

    def test_done(self):
        """Verify the done queryset."""
        # Create a question, there shouldn't be any done yet.
        q = question(save=True)
        eq_(0, Question.objects.done().count())

        # Add an answer, there shouldn't be any done yet.
        a = answer(question=q, save=True)
        eq_(0, Question.objects.done().count())

        # Make it the solution, there should be one done.
        q.solution = a
        q.save()
        eq_(1, Question.objects.done().count())

        # Create a locked questions, there should be two done.
        question(is_locked=True, save=True)
        eq_(2, Question.objects.done().count())

    def test_responded(self):
        """Verify the responded queryset."""
        # Create a question, there shouldn't be any responded yet.
        q = question(save=True)
        eq_(0, Question.objects.responded().count())

        # Add an answer, there should be one responded.
        a = answer(question=q, save=True)
        eq_(1, Question.objects.responded().count())

        # Add an answer by the creator, there should be none responded.
        a = answer(creator=q.creator, question=q, save=True)
        eq_(0, Question.objects.responded().count())

        # Add another answer, there should be one responded.
        a = answer(question=q, save=True)
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
        q = question(save=True)
        eq_(1, Question.objects.needs_attention().count())

        # Add an answer, there should be no needs_attention.
        a = answer(question=q, save=True)
        eq_(0, Question.objects.needs_attention().count())

        # Add an answer by the creator, there should be one needs_attention.
        a = answer(creator=q.creator, question=q, save=True)
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
        q = question(save=True)

        # There should be no needs_info questions yet.
        eq_(0, Question.objects.needs_info().count())

        # Tag a question and there should be one needs_info question.
        q.set_needs_info()
        eq_(1, Question.objects.needs_info().count())

        # Remove tag and there shouldn't be any anymore.
        q.unset_needs_info()
        eq_(0, Question.objects.needs_info().count())

    def test_escalated(self):
        """Verify the escalated queryset."""
        t = tag(
            name=config.ESCALATE_TAG_NAME,
            slug=config.ESCALATE_TAG_NAME,
            save=True)
        q = question(save=True)

        # There should be no escalated questions yet.
        eq_(0, Question.objects.escalated().count())

        # Tag a question and there should be one escalated question.
        q.tags.add(t)
        eq_(1, Question.objects.escalated().count())
