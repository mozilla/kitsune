from nose.tools import eq_

from products.tests import product
from questions.models import Question
from questions.tests import question, answer, answervote, questionvote
from search.tests.test_es import ElasticTestCase
from topics.tests import topic


class QuestionUpdateTests(ElasticTestCase):
    def test_added(self):
        # Create a question--that adds one document to the index.
        q = question(title=u'Does this test work?', save=True)
        self.refresh()
        eq_(Question.search().query(
                or_=dict(('%s__text' % field, 'test')
                         for field in Question.get_query_fields())).count(),
            1)

        # Create an answer for the question. It shouldn't be searchable
        # until the answer is saved.
        a = answer(content=u'There\'s only one way to find out!',
                   question=q)
        self.refresh()
        eq_(Question.search().query(
                or_=dict(('%s__text' % field, 'only')
                         for field in Question.get_query_fields())).count(),
            0)

        a.save()
        self.refresh()
        eq_(Question.search().query(
                or_=dict(('%s__text' % field, 'only')
                         for field in Question.get_query_fields())).count(),
            1)

        # Make sure that there's only one question document in the
        # index--creating an answer should have updated the existing
        # one.
        eq_(Question.search().count(), 1)

    def test_question_no_answers_deleted(self):
        q = question(title=u'Does this work?', save=True)
        self.refresh()
        eq_(Question.search().query(question_title__text='work').count(), 1)

        q.delete()
        self.refresh()
        eq_(Question.search().query(question_title__text='work').count(), 0)

    def test_question_one_answer_deleted(self):
        q = question(title=u'are model makers the new pink?', save=True)
        a = answer(content=u'yes.', question=q, save=True)
        self.refresh()

        # Question and its answers are a single document--so the
        # index count should be only 1.
        eq_(Question.search().query(question_title__text='pink').count(), 1)

        # After deleting the answer, the question document should
        # remain.
        a.delete()
        self.refresh()
        eq_(Question.search().query(question_title__text='pink').count(), 1)

        # Delete the question and it should be removed from the
        # index.
        q.delete()
        self.refresh()
        eq_(Question.search().query(question_title__text='pink').count(), 0)

    def test_question_questionvote(self):
        # Create a question and verify it doesn't show up in a
        # query for num_votes__gt=0.
        q = question(title=u'model makers will inherit the earth', save=True)
        self.refresh()
        eq_(Question.search().filter(question_num_votes__gt=0).count(), 0)

        # Add a QuestionVote--it should show up now.
        questionvote(question=q, save=True)
        self.refresh()
        eq_(Question.search().filter(question_num_votes__gt=0).count(), 1)

    def test_questions_tags(self):
        """Make sure that adding tags to a Question causes it to
        refresh the index.

        """
        tag = u'hiphop'
        eq_(Question.search().filter(question_tag=tag).count(), 0)
        q = question(save=True)
        self.refresh()
        eq_(Question.search().filter(question_tag=tag).count(), 0)
        q.tags.add(tag)
        self.refresh()
        eq_(Question.search().filter(question_tag=tag).count(), 1)
        q.tags.remove(tag)
        self.refresh()
        eq_(Question.search().filter(question_tag=tag).count(), 0)

    def test_question_topics(self):
        """Make sure that adding topics to a Question causes it to
        refresh the index.

        """
        t = topic(slug=u'hiphop', save=True)
        eq_(Question.search().filter(topic=t.slug).count(), 0)
        q = question(save=True)
        self.refresh()
        eq_(Question.search().filter(topic=t.slug).count(), 0)
        q.topics.add(t)
        self.refresh()
        eq_(Question.search().filter(topic=t.slug).count(), 1)
        q.topics.clear()
        self.refresh()

        # Make sure the question itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(Question.search().filter().count(), 1)

        eq_(Question.search().filter(topic=t.slug).count(), 0)

    def test_question_products(self):
        """Make sure that adding products to a Question causes it to
        refresh the index.

        """
        p = product(slug=u'desktop', save=True)
        eq_(Question.search().filter(product=p.slug).count(), 0)
        q = question(save=True)
        self.refresh()
        eq_(Question.search().filter(product=p.slug).count(), 0)
        q.products.add(p)
        self.refresh()
        eq_(Question.search().filter(product=p.slug).count(), 1)
        q.products.remove(p)
        self.refresh()

        # Make sure the question itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(Question.search().filter().count(), 1)

        eq_(Question.search().filter(product=p.slug).count(), 0)


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
        result = Question.search().query(question_title__text='LOLRUS',
                                         question_content__text='LOLRUS')
        assert result.count() > 0
