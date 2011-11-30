from questions.tests import ESTestCase
from questions.models import Question

import elasticutils
import uuid

from nose.tools import eq_


class TestQuestionUpdate(ESTestCase):
    def test_added(self):
        # Use a uuid since it's "unique" and makes sure we're not
        # accidentally picking up a Question we don't want.
        title = str(uuid.uuid4())
        question = Question(title=title,
                            content='Lorem Ipsum Dolor',
                            creator_id=118533)

        # Assert that it's not in the index before saving.
        eq_(elasticutils.S(Question).query(title=title).count(), 0)

        question.save()

        # It's in the index now.
        eq_(elasticutils.S(Question).query(title=title).count(), 1)
