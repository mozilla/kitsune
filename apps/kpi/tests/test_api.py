from datetime import date
import json

from nose.tools import eq_

from kpi.models import Metric
from kpi.tests import metric, metric_kind
from questions.tests import question, answer
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from questions.tests import answer, answer_vote
from users.tests import user, add_permission
from users.models import Profile
from wiki.tests import revision, helpful_vote


class KpiApiTests(TestCase):
    client_class = LocalizingClient

    def _log_in_as_permissioned(self, permission='view_kpi_dashboard'):
        """Log in as a user with the ``view_kpi_dashboard`` permission."""
        u = user(save=True)
        add_permission(u, Profile, permission)
        self.client.login(username=u.username, password='testpass')

    def _make_sphinx_metric_kinds(self):
        click_kind = metric_kind(code='search clickthroughs:sphinx:clicks',
                                 save=True)
        search_kind = metric_kind(code='search clickthroughs:sphinx:searches',
                                  save=True)
        return click_kind, search_kind

    def test_solved(self):
        """Test solved API call."""
        self._log_in_as_permissioned()

        a = answer(save=True)
        a.question.solution = a
        a.question.save()

        question(save=True)

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_solution',
                              'api_name': 'v1'})
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['questions'], 2)

    def test_vote(self):
        """Test vote API call."""
        self._log_in_as_permissioned()

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
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)
        eq_(r['objects'][0]['ans_helpful'], 2)
        eq_(r['objects'][0]['ans_votes'], 3)

    def test_fast_response(self):
        """Test fast response API call."""
        self._log_in_as_permissioned()

        a = answer(save=True)
        a.question.solution = a
        a.question.save()

        a = answer(save=True)
        a.question.save()

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_fast_response',
                              'api_name': 'v1'})
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['responded'], 2)
        eq_(r['objects'][0]['questions'], 2)

    def test_sphinx_clickthrough_get(self):
        """Test Sphinx clickthrough read API."""
        self._log_in_as_permissioned()

        click_kind, search_kind = self._make_sphinx_metric_kinds()
        metric(kind=click_kind,
               start=date(2000, 1, 1),
               value=1,
               save=True)
        metric(kind=search_kind,
               start=date(2000, 1, 1),
               value=10,
               save=True)
        metric(kind=click_kind,
               start=date(2000, 1, 9),
               value=2,
               save=True)
        metric(kind=search_kind,
               start=date(2000, 1, 9),
               value=20,
               save=True)

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'sphinx-clickthrough-rate',
                              'api_name': 'v1'})
        response = self.client.get(url + '?format=json')
        # Beware of dict order changes someday.
        self.assertContains(response, '''"objects": [{"clicks": 1, "resource_uri": "", "searches": 10, "start": "2000-01-01"}, {"clicks": 2, "resource_uri": "", "searches": 20, "start": "2000-01-09"}]''')

    def test_sphinx_clickthrough_post(self):
        """Test Sphinx clickthrough write API."""
        self._log_in_as_permissioned('change_metric')

        click_kind, search_kind = self._make_sphinx_metric_kinds()

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'sphinx-clickthrough-rate',
                              'api_name': 'v1'})
        response = self.client.post(url,
                                    json.dumps({'start': '2000-01-02',
                                                'searches': 1e8,
                                                'clicks': 5e7}),
                                    content_type='application/json')
        eq_(response.status_code, 201)

        # Do a GET, and see if the round trip worked:
        self._log_in_as_permissioned()
        response = self.client.get(url + '?format=json')
        self.assertContains(
            response,
            '''"objects": [{"clicks": 50000000, "resource_uri": "", "searches": 100000000, "start": "2000-01-02"}]''')
