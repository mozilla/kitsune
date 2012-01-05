import elasticutils
from nose.tools import eq_
from waffle.models import Flag

from questions.models import Question, question_searcher
from questions.tests import question, answer, answer_vote
from search.tests import dummy_request
from sumo.tests import ElasticTestCase


class QuestionUpdateTests(ElasticTestCase):
    def test_added(self):
        eq_(elasticutils.S(Question).count(), 0)

        q = question(save=True)
        eq_(elasticutils.S(Question).count(), 1)

        a = answer(question=q)
        eq_(elasticutils.S(Question).count(), 1)

        a.save()
        self.refresh()

        # Creating a new answer for a question doesn't create a new
        # document in the index.  Therefore, the count remains 1.
        #
        # TODO: This is ambiguous: it's not clear whether we correctly
        # updated the document in the index or whether the post_save
        # hook didn't kick off.  Need a better test.
        eq_(elasticutils.S(Question).count(), 1)

    def test_question_no_answers_deleted(self):
        eq_(elasticutils.S(Question).count(), 0)

        q = question(save=True)
        self.refresh()
        eq_(elasticutils.S(Question).count(), 1)

        q.delete()
        self.refresh()
        eq_(elasticutils.S(Question).count(), 0)

    def test_question_one_answer_deleted(self):
        eq_(elasticutils.S(Question).count(), 0)

        q = question(save=True)
        a = answer(question=q, save=True)
        self.refresh()

        # Question and its answers are a single document--so the
        # index count should be only 1.
        eq_(elasticutils.S(Question).count(), 1)

        a.delete()
        self.refresh()
        eq_(elasticutils.S(Question).count(), 1)

        q.delete()
        self.refresh()
        eq_(elasticutils.S(Question).count(), 0)


class QuestionSearchTests(ElasticTestCase):
    """Tests about searching for questions"""
    def test_case_insensitive_search(self):
        """Ensure the default searcher is case insensitive."""
        Flag.objects.create(name='elasticsearch', everyone=True)
        answer_vote(
            answer=answer(question=question(title='lolrus',
                                            content='I am the lolrus.',
                                            save=True),
                          save=True),
            helpful=True).save()
        result = question_searcher(dummy_request).query('LOLRUS')
        assert len(result) > 0
