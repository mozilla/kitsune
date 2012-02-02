from datetime import datetime
import json

from nose.tools import eq_

from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from questions.tests import answer, answer_vote, question
from users.tests import user
from wiki.tests import document, revision, helpful_vote


class KpiAPITests(TestCase):
    client_class = LocalizingClient

    def test_solved(self):
        """Test solved API call."""
        u = user(save=True)

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

    def test_fast_response(self):
        """Test fast response API call."""
        u = user(save=True)

        a = answer(save=True)
        a.question.solution = a
        a.question.save()

        a = answer(save=True)
        a.question.save()

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_fast_response',
                              'api_name': 'v1'})
        self.client.login(username=u.username, password='testpass')
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['responded'], 2)
        eq_(r['objects'][0]['questions'], 2)

    def test_active_kb_contributors(self):
        """Test active kb contributors API call."""
        r1 = revision(creator=user(save=True), save=True)
        r2 = revision(creator=user(save=True), save=True)

        d = document(parent=r1.document, locale='es', save=True)
        revision(document=d, reviewed=datetime.now(),
                 reviewer=r1.creator, creator=r2.creator, save=True)

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_active_kb_contributors',
                              'api_name': 'v1'})

        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['en_us'], 2)
        eq_(r['objects'][0]['non_en_us'], 2)
