import uuid

import elasticutils
from nose.tools import eq_
from waffle.models import Flag

from questions.models import Question, Answer, question_searcher
from questions.tests import ESTestCase
from search.tests import dummy_request


class QuestionUpdateTests(ESTestCase):
    def test_added(self):
        title = str(uuid.uuid4())
        question = Question(title=title,
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)

        original_count = elasticutils.S(Question).count()

        question.save()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count + 1)

        answer = Answer(content=u'Answer to ' + title,
                        question=question,
                        creator_id=118533)

        eq_(elasticutils.S(Question).count(), original_count + 1)

        answer.save()
        self.refresh()

        # Creating a new answer for a question doesn't create a new
        # document in the index.  Therefore, the count remains
        # original_count + 1.
        #
        # TODO: This is ambiguous: it's not clear whether we correctly
        # updated the document in the index or whether the post_save
        # hook didn't kick off.  Need a better test.
        eq_(elasticutils.S(Question).count(), original_count + 1)

    def test_question_no_answers_deleted(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        title = str(uuid.uuid4())

        original_count = elasticutils.S(Question).count()

        question = Question(title=title,
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)
        question.save()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count + 1)

        question.delete()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count)

    def test_question_one_answer_deleted(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Post we don't want.
        title = str(uuid.uuid4())

        original_count = elasticutils.S(Question).count()

        question = Question(title=title,
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)
        question.save()

        answer = Answer(content=u'Answer to ' + title,
                        question=question,
                        creator_id=118533)

        answer.save()
        self.refresh()

        # Question and its answers are a single document--so the
        # index count shouldn't change.
        eq_(elasticutils.S(Question).count(), original_count + 1)

        answer.delete()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count + 1)

        question.delete()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count)


class QuestionSearchTests(ESTestCase):
    """Tests about searching for questions"""
    def test_case_insensitive_search(self):
        """Ensure the default searcher is case insensitive."""
        Flag.objects.create(name='elasticsearch', everyone=True)
        result = question_searcher(dummy_request).query('LOLRUS')
        assert len(result) > 0
