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

        url = reverse('api_dispatch_list', kwargs={'resource_name': 'solution', 'api_name' :'v1'})
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r, {u'meta': {u'previous': None,
                          u'total_count': 1,
                          u'offset': 0,
                          u'limit': 20,
                          u'next': None},
                u'objects': [{u'date': u'2012-01-01',
                              u'without_solutions': 0,
                              u'with_solutions': 1,
                              u'resource_uri': u''}]})
