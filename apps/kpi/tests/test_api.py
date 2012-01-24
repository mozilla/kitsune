import json

from nose.tools import eq_

from questions.tests import question, answer
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from questions.tests import answer, answer_vote
from users.tests import user, add_permission
from users.models import Profile
from wiki.tests import revision, helpful_vote


class KpiAPITests(TestCase):
    client_class = LocalizingClient

    def test_solved(self):
        """Test solved API call."""
        u = user(save=True)
        add_permission(u, Profile, 'view_kpi_dashboard')

        a = answer(save=True)
        a.question.solution = a
        a.question.save()

        question(save=True)

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_solution',
                              'api_name': 'v1'})
        self.client.login(username=u.username, password='testpass')
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['questions'], 2)

    def test_vote(self):
        """Test vote API call."""
        u = user(save=True)
        add_permission(u, Profile, 'view_kpi_dashboard')

        r = revision(save=True)
        helpful_vote(revision=r, save=True)
        helpful_vote(revision=r, save=True)
        helpful_vote(revision=r, helpful=True, save=True)

        a = answer(save=True)
        answer_vote(answer=a, save=True)
        answer_vote(answer=a, helpful=True, save=True)
        answer_vote(answer=a, helpful=True, save=True)

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_vote',
                              'api_name': 'v1'})
        self.client.login(username=u.username, password='testpass')
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)
        eq_(r['objects'][0]['ans_helpful'], 2)
        eq_(r['objects'][0]['ans_votes'], 3)
