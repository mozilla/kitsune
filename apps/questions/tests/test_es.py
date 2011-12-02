from questions.tests import ESTestCase
from questions.models import Question, Answer

import elasticutils
import uuid

from nose.tools import eq_


class TestQuestionUpdate(ESTestCase):
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

        eq_(elasticutils.S(Question).count(), original_count + 2)

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

        eq_(elasticutils.S(Question).count(), original_count + 2)

        answer.delete()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count + 1)

        question.delete()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count)
