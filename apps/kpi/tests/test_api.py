from base64 import b64encode
from datetime import date, datetime, timedelta
import json

from django.core.cache import cache

from nose.tools import eq_

from customercare.tests import reply
from kpi.cron import update_contributor_metrics
from kpi.models import (Metric,
                        AOA_CONTRIBUTORS_METRIC_CODE,
                        KB_ENUS_CONTRIBUTORS_METRIC_CODE,
                        KB_L10N_CONTRIBUTORS_METRIC_CODE,
                        L10N_METRIC_CODE,
                        SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE,
                        VISITORS_METRIC_CODE)

from kpi.tests import metric, metric_kind
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from questions.tests import answer, answervote, question
from users.tests import user, add_permission
from wiki.tests import document, revision, helpful_vote


class KpiApiTests(TestCase):
    client_class = LocalizingClient

    def _make_elastic_metric_kinds(self):
        click_kind = metric_kind(code='search clickthroughs:elastic:clicks',
                                 save=True)
        search_kind = metric_kind(code='search clickthroughs:elastic:searches',
                                  save=True)
        return click_kind, search_kind

    def _make_contributor_metric_kinds(self):
        metric_kind(code=AOA_CONTRIBUTORS_METRIC_CODE, save=True)
        metric_kind(code=KB_ENUS_CONTRIBUTORS_METRIC_CODE, save=True)
        metric_kind(code=KB_L10N_CONTRIBUTORS_METRIC_CODE, save=True)
        metric_kind(code=SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE, save=True)

    def _get_api_result(self, resource_name):
        """Helper to make API calls, parse the json and return the result."""
        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': resource_name,
                              'api_name': 'v1'})
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        return json.loads(response.content)

    def test_questions(self):
        """Test questions API call."""
        # A question with a solution:
        a = answer(save=True)
        a.question.solution = a
        a.question.save()
        # A question with an answer:
        answer(save=True)
        # A question without answers:
        question(save=True)

        r = self._get_api_result('kpi_questions')
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['responded_24'], 2)
        eq_(r['objects'][0]['responded_72'], 2)
        eq_(r['objects'][0]['questions'], 3)

    def test_questions_inactive_user(self):
        """Verify questions from inactive users aren't counted."""
        # Two questions for an inactive user.
        # They shouldn't show up in the count.
        u = user(is_active=False, save=True)
        question(creator=u, save=True)
        question(creator=u, save=True)

        r = self._get_api_result('kpi_questions')
        eq_(len(r['objects']), 0)

        # Activate the user, now the questions should count.
        u.is_active = True
        u.save()
        cache.clear()  # We need to clear the cache for new results.

        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'kpi_questions',
                              'api_name': 'v1'})
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['questions'], 2)

    def test_vote(self):
        """Test vote API call."""
        r = revision(save=True)
        helpful_vote(revision=r, save=True)
        helpful_vote(revision=r, save=True)
        helpful_vote(revision=r, helpful=True, save=True)

        a = answer(save=True)
        answervote(answer=a, save=True)
        answervote(answer=a, helpful=True, save=True)
        answervote(answer=a, helpful=True, save=True)

        r = self._get_api_result('kpi_vote')
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)
        eq_(r['objects'][0]['ans_helpful'], 2)
        eq_(r['objects'][0]['ans_votes'], 3)

    def test_kb_vote(self):
        """Test vote API call."""
        r1 = revision(document=document(locale='en-US', save=True), save=True)
        r2 = revision(document=document(locale='es', save=True), save=True)
        for r in [r1, r2]:
            helpful_vote(revision=r, save=True)
            helpful_vote(revision=r, save=True)
            helpful_vote(revision=r, helpful=True, save=True)

        # Only the votes for r1 (locale=en-US) should be counted.
        r = self._get_api_result('kpi_kb_vote')
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)

    def test_active_contributors(self):
        """Test active contributors API call."""
        # 2 en-US revisions by 2 contributors:
        r1 = revision(creator=user(save=True), save=True)
        r2 = revision(creator=user(save=True), save=True)
        # A translation with 2 contributors (translator + reviewer):
        d = document(parent=r1.document, locale='es', save=True)
        revision(document=d, reviewed=datetime.now(),
                 reviewer=r1.creator, creator=r2.creator, save=True)
        # 1 active support forum contributor:
        # A user with 10 answers
        u1 = user(save=True)
        for x in range(10):
            answer(save=True, creator=u1)
        # A user with 9 answers
        u2 = user(save=True)
        for x in range(9):
            answer(save=True, creator=u2)
        # A user with 1 answer
        u3 = user(save=True)
        answer(save=True, creator=u3)

        # An AoA reply (1 contributor):
        reply(save=True)

        # Create metric kinds and update metrics for tomorrow (today's
        # activity shows up tomorrow).
        self._make_contributor_metric_kinds()
        update_contributor_metrics(day=date.today() + timedelta(days=1))

        r = self._get_api_result('kpi_active_contributors')

        eq_(r['objects'][0]['en_us'], 2)
        eq_(r['objects'][0]['non_en_us'], 2)
        eq_(r['objects'][0]['support_forum'], 1)
        eq_(r['objects'][0]['aoa'], 1)

    def test_asker_replies_arent_a_contribution(self):
        """Verify that replies posted by the question creator aren't counted.

        If a user has 10 replies to their own question, they aren't counted as
        a contributor.
        """
        # A user with 10 answers to own question.
        q = question(save=True)
        u = q.creator
        for x in range(10):
            answer(creator=u, question=q, save=True)

        # Create metric kinds and update metrics for tomorrow (today's
        # activity shows up tomorrow).
        self._make_contributor_metric_kinds()
        update_contributor_metrics(day=date.today() + timedelta(days=1))

        r = self._get_api_result('kpi_active_contributors')
        eq_(r['objects'][0]['support_forum'], 0)

        # Change the question creator, now we should have 1 contributor.
        q.creator = user(save=True)
        q.save()
        cache.clear()  # We need to clear the cache for new results.

        Metric.objects.all().delete()
        update_contributor_metrics(day=date.today() + timedelta(days=1))

        r = self._get_api_result('kpi_active_contributors')
        eq_(r['objects'][0]['support_forum'], 1)

    def test_elastic_clickthrough_get(self):
        """Test elastic clickthrough read API."""
        click_kind, search_kind = self._make_elastic_metric_kinds()
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
                      kwargs={'resource_name': 'elastic-clickthrough-rate',
                              'api_name': 'v1'})
        response = self.client.get(url + '?format=json')
        self.assertContains(  # Beware of dict order changes someday.
            response,
            '"objects": [{"clicks": 2, "resource_uri": "", "searches": 20, '
                         '"start": "2000-01-09"}, '
                        '{"clicks": 1, "resource_uri": "", "searches": 10, '
                         '"start": "2000-01-01"}]')

        # Test filtering by start date:
        response = self.client.get(url + '?format=json&min_start=2000-01-09')
        self.assertContains(  # Beware of dict order changes someday.
            response,
            '"objects": [{"clicks": 2, "resource_uri": "", "searches": 20, '
                         '"start": "2000-01-09"}]')

    def test_elastic_clickthrough_post(self):
        """Test elastic clickthrough write API."""
        u = user(save=True)
        add_permission(u, Metric, 'add_metric')

        click_kind, search_kind = self._make_elastic_metric_kinds()

        # POST the new object:
        url = reverse('api_dispatch_list',
                      kwargs={'resource_name': 'elastic-clickthrough-rate',
                              'api_name': 'v1'})
        auth = 'Basic ' + b64encode('%s:%s' % (u.username, 'testpass'))
        response = self.client.post(url,
                                    json.dumps({'start': '2000-01-02',
                                                'searches': 1e8,
                                                'clicks': 5e7}),
                                    content_type='application/json',
                                    HTTP_AUTHORIZATION=auth)
        eq_(response.status_code, 201)

        # Do a GET, and see if the round trip worked:
        response = self.client.get(url + '?format=json')
        self.assertContains(  # Beware of dict order changes someday.
            response,
            '"objects": [{"clicks": 50000000, "resource_uri": "", '
                         '"searches": 100000000, "start": "2000-01-02"}]')

        # Correspnding ElasticSearch APIs are likely correct by dint
        # of factoring.

    def test_visitors(self):
        """Test unique visitors API call."""
        # Create the metric.
        kind = metric_kind(code=VISITORS_METRIC_CODE, save=True)
        metric(kind=kind, start=date.today(), end=date.today(), value=42,
               save=True)

        # There should be 42 visitors.
        r = self._get_api_result('kpi_visitors')
        eq_(r['objects'][0]['visitors'], 42)

    def test_l10n_coverage(self):
        """Test l10n coverage API call."""
        # Create the metrics
        kind = metric_kind(code=L10N_METRIC_CODE, save=True)
        metric(kind=kind, start=date.today(), end=date.today(), value=56,
               save=True)

        # The l10n coverage should be 56%.
        r = self._get_api_result('kpi_l10n_coverage')
        eq_(r['objects'][0]['coverage'], 56)
