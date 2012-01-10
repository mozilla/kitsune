import json

import mock
from nose.tools import eq_
import waffle

from questions.models import Question, Answer, User

from sumo.helpers import urlparams
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.tests import user


class KpiAPITests(TestCase):
    client_class = LocalizingClient

    @mock.patch.object(waffle, 'switch_is_active')
    def test_percent(self, switch_is_active):
        """Test user API with all defaults."""
        switch_is_active.return_value = True
        u = user()
        u.save()
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=u.id)
        question.save()
        answer = Answer(question=question, creator_id=u.id,
                        content="Test Answer")
        answer.save()

        question.solution = answer
        question.save()

        url = reverse('kpi.api.percent_answered')
        response = self.client.get(url)
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r, {'data': {'solutions': 1,
                         'without_solutions': 0},
                'success': True})
