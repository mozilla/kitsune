from nose.tools import eq_

from kitsune.products.tests import product, topic
from kitsune.questions.models import QuestionMappingType
from kitsune.questions.tests import question, answer, answervote, questionvote
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.tests import user


class QuestionUpdateTests(ElasticTestCase):
    def test_added(self):
        search = QuestionMappingType.search()

        # Create a question--that adds one document to the index.
        q = question(title=u'Does this test work?', save=True)
        self.refresh()
        query = dict(('%s__text' % field, 'test')
                     for field in QuestionMappingType.get_query_fields())
        eq_(search.query(should=True, **query).count(), 1)

        # Create an answer for the question. It shouldn't be searchable
        # until the answer is saved.
        a = answer(content=u'There\'s only one way to find out!',
                   question=q)
        self.refresh()
        query = dict(('%s__text' % field, 'only')
                     for field in QuestionMappingType.get_query_fields())
        eq_(search.query(should=True, **query).count(), 0)

        a.save()
        self.refresh()
        query = dict(('%s__text' % field, 'only')
                     for field in QuestionMappingType.get_query_fields())
        eq_(search.query(should=True, **query).count(), 1)

        # Make sure that there's only one question document in the
        # index--creating an answer should have updated the existing
        # one.
        eq_(search.count(), 1)

    def test_question_no_answers_deleted(self):
        search = QuestionMappingType.search()

        q = question(title=u'Does this work?', save=True)
        self.refresh()
        eq_(search.query(question_title__text='work').count(), 1)

        q.delete()
        self.refresh()
        eq_(search.query(question_title__text='work').count(), 0)

    def test_question_one_answer_deleted(self):
        search = QuestionMappingType.search()

        q = question(title=u'are model makers the new pink?', save=True)
        a = answer(content=u'yes.', question=q, save=True)
        self.refresh()

        # Question and its answers are a single document--so the
        # index count should be only 1.
        eq_(search.query(question_title__text='pink').count(), 1)

        # After deleting the answer, the question document should
        # remain.
        a.delete()
        self.refresh()
        eq_(search.query(question_title__text='pink').count(), 1)

        # Delete the question and it should be removed from the
        # index.
        q.delete()
        self.refresh()
        eq_(search.query(question_title__text='pink').count(), 0)

    def test_question_questionvote(self):
        search = QuestionMappingType.search()

        # Create a question and verify it doesn't show up in a
        # query for num_votes__gt=0.
        q = question(title=u'model makers will inherit the earth', save=True)
        self.refresh()
        eq_(search.filter(question_num_votes__gt=0).count(), 0)

        # Add a QuestionVote--it should show up now.
        questionvote(question=q, save=True)
        self.refresh()
        eq_(search.filter(question_num_votes__gt=0).count(), 1)

    def test_questions_tags(self):
        """Make sure that adding tags to a Question causes it to
        refresh the index.

        """
        tag = u'hiphop'
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 0)
        q = question(save=True)
        self.refresh()
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 0)
        q.tags.add(tag)
        self.refresh()
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 1)
        q.tags.remove(tag)
        self.refresh()
        eq_(QuestionMappingType.search().filter(question_tag=tag).count(), 0)

    def test_question_topics(self):
        """Make sure that adding topics to a Question causes it to
        refresh the index.

        """
        p = product(save=True)
        t = topic(slug=u'hiphop', product=p, save=True)
        eq_(QuestionMappingType.search().filter(topic=t.slug).count(), 0)
        q = question(save=True)
        self.refresh()
        eq_(QuestionMappingType.search().filter(topic=t.slug).count(), 0)
        q.topics.add(t)
        self.refresh()
        eq_(QuestionMappingType.search().filter(topic=t.slug).count(), 1)
        q.topics.clear()
        self.refresh()

        # Make sure the question itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(QuestionMappingType.search().filter().count(), 1)

        eq_(QuestionMappingType.search().filter(topic=t.slug).count(), 0)

    def test_question_products(self):
        """Make sure that adding products to a Question causes it to
        refresh the index.

        """
        p = product(slug=u'desktop', save=True)
        eq_(QuestionMappingType.search().filter(product=p.slug).count(), 0)
        q = question(save=True)
        self.refresh()
        eq_(QuestionMappingType.search().filter(product=p.slug).count(), 0)
        q.products.add(p)
        self.refresh()
        eq_(QuestionMappingType.search().filter(product=p.slug).count(), 1)
        q.products.remove(p)
        self.refresh()

        # Make sure the question itself is still there and that we didn't
        # accidentally delete it through screwed up signal handling:
        eq_(QuestionMappingType.search().filter().count(), 1)

        eq_(QuestionMappingType.search().filter(product=p.slug).count(), 0)

    def test_question_is_unindexed_on_creator_delete(self):
        search = QuestionMappingType.search()

        q = question(title=u'Does this work?', save=True)
        self.refresh()
        eq_(search.query(question_title__text='work').count(), 1)

        q.creator.delete()
        self.refresh()
        eq_(search.query(question_title__text='work').count(), 0)

    def test_question_is_reindexed_on_username_change(self):
        search = QuestionMappingType.search()

        u = user(username='dexter', save=True)

        q = question(creator=u, title=u'Hello', save=True)
        a = answer(creator=u, content=u'I love you', save=True)
        self.refresh()
        eq_(search.query(question_title__text='hello')[0]['question_creator'],
            u'dexter')
        query = search.query(question_answer_content__text='love')
        eq_(query[0]['question_answer_creator'],
            [u'dexter'])

        # NOTE: This doesn't work because we depend on the countdown in celery.
        # Any ideas?
        # Change the username and verify the index.
        # u.username = 'walter'
        # u.save()
        # self.refresh()
        # eq_(search.query(question_title__text='hello')[0]['question_creator'],
        #     u'walter')
        # eq_(search.query(question_answer_content__text='love')[0]['question_answer_creator'],
        #     [u'walter'])


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
        result = QuestionMappingType.search().query(
            question_title__text='LOLRUS',
            question_content__text='LOLRUS')
        assert result.count() > 0
