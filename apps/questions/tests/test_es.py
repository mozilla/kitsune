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

        original_count = elasticutils.S(Question).count()

        question.save()
        self.refresh()

        eq_(elasticutils.S(Question).count(), original_count + 1)
