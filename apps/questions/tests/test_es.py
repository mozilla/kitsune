import elasticutils
from nose.tools import eq_

from questions.models import Question, question_searcher
from questions.tests import question, answer, answervote, questionvote
from search.tests import dummy_request
from sumo.tests import ElasticTestCase


class QuestionUpdateTests(ElasticTestCase):
    def test_added(self):
        # Create a question--that adds one document to the index.
        q = question(title=u'Does this test work?', save=True)
        self.refresh()
        eq_(question_searcher(dummy_request).query('test').count(), 1)

        # Create an answer for the question. It shouldn't be searchable
        # until the answer is saved.
        a = answer(content=u'There\'s only one way to find out!',
                   question=q)
        self.refresh()
        eq_(question_searcher(dummy_request).query('only').count(), 0)

        a.save()
        self.refresh()
        eq_(question_searcher(dummy_request).query('only').count(), 1)

        # Make sure that there's only one question document in the
        # index--creating an answer should have updated the existing
        # one.
        eq_(elasticutils.S(Question).count(), 1)

    def test_question_no_answers_deleted(self):
        q = question(title=u'Does this work?', save=True)
        self.refresh()
        eq_(question_searcher(dummy_request).query('work').count(), 1)

        q.delete()
        self.refresh()
        eq_(question_searcher(dummy_request).query('work').count(), 0)

    def test_question_one_answer_deleted(self):
        q = question(title=u'are model makers the new pink?', save=True)
        a = answer(content=u'yes.', question=q, save=True)
        self.refresh()

        # Question and its answers are a single document--so the
        # index count should be only 1.
        eq_(question_searcher(dummy_request).query('pink').count(), 1)

        # After deleting the answer, the question document should
        # remain.
        a.delete()
        self.refresh()
        eq_(question_searcher(dummy_request).query('pink').count(), 1)

        # Delete the question and it should be removed from the
        # index.
        q.delete()
        self.refresh()
        eq_(question_searcher(dummy_request).query('pink').count(), 0)

    def test_question_questionvote(self):
        # Create a question and verify it doesn't show up in a
        # query for num_votes__gt=0.
        q = question(title=u'model makers will inherit the earth', save=True)
        self.refresh()
        eq_(question_searcher(dummy_request).filter(num_votes__gt=0).count(), 0)

        # Add a QuestionVote--it should show up now.
        qv = questionvote(question=q, save=True)
        self.refresh()
        eq_(question_searcher(dummy_request).filter(num_votes__gt=0).count(), 1)

    def test_questions_tags(self):
        """Make sure that adding tags to a Question causes it to
        refresh the index.

        """
        tag = u'hiphop'
        eq_(elasticutils.S(Question).filter(tag=tag).count(), 0)
        q = question(save=True)
        self.refresh()
        eq_(elasticutils.S(Question).filter(tag=tag).count(), 0)
        q.tags.add(tag)
        self.refresh()
        eq_(elasticutils.S(Question).filter(tag=tag).count(), 1)
        q.tags.remove(tag)
        self.refresh()
        eq_(elasticutils.S(Question).filter(tag=tag).count(), 0)


class QuestionSearchTests(ElasticTestCase):
    """Tests about searching for questions"""
    def test_case_insensitive_search(self):
        """Ensure the default searcher is case insensitive."""
        answervote(
            answer=answer(question=question(title='lolrus',
                                            content='I am the lolrus.',
                                            save=True),
                          save=True),
            helpful=True).save()
        self.refresh()
        result = question_searcher(dummy_request).query('LOLRUS')
        assert len(result) > 0
