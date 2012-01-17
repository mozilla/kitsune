import json

import mock
from nose.tools import eq_
import waffle

from questions.models import Question, Answer, User
from users.models import Profile

from sumo.helpers import urlparams
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.tests import user, add_permission


class KpiAPITests(TestCase):
    client_class = LocalizingClient

    @mock.patch.object(waffle, 'switch_is_active')
    def test_percent(self, switch_is_active):
        """Test user API with all defaults."""
        switch_is_active.return_value = True
        u = user()
        u.save()
        add_permission(u, models.Profile , 'view_dashboard')
import json

import mock
from nose.tools import eq_
import waffle

from questions.models import Question, Answer, User

from sumo.helpers import urlparams
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.tests import user, add_permission
from users.models import Profile

class KpiAPITests(TestCase):
    client_class = LocalizingClient

    @mock.patch.object(waffle, 'switch_is_active')
    def test_percent(self, switch_is_active):
        """Test user API with all defaults."""
        switch_is_active.return_value = True
        u = user()
        u.save()
        add_permission(u, Profile, 'view_kpi_dashboard')
        question = Question(title='Test Question',
                            content='Lorem Ipsum Dolor',
                            creator_id=u.id)
        question.save()
        answer = Answer(question=question, creator_id=u.id,
                        content="Test Answer")
        answer.save()

        question.solution = answer
        question.save()

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_solution',
                              'api_name': 'v1'})
        self.client.login(username=u.username, password='testpass')
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['with_solutions'], 1)
        eq_(r['objects'][0]['without_solutions'], 0)
