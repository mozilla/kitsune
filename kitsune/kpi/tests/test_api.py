from datetime import date, datetime, timedelta
import json

from django.core.cache import cache

from nose.tools import eq_

from kitsune.customercare.tests import ReplyFactory
from kitsune.kpi.cron import update_contributor_metrics
from kitsune.kpi.models import (
    Metric, AOA_CONTRIBUTORS_METRIC_CODE, KB_ENUS_CONTRIBUTORS_METRIC_CODE,
    KB_L10N_CONTRIBUTORS_METRIC_CODE, L10N_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE, VISITORS_METRIC_CODE,
    EXIT_SURVEY_YES_CODE, EXIT_SURVEY_NO_CODE, EXIT_SURVEY_DONT_KNOW_CODE)
from kitsune.kpi.tests import MetricFactory, MetricKindFactory
from kitsune.products.tests import ProductFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.questions.tests import AnswerFactory, AnswerVoteFactory, QuestionFactory
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import DocumentFactory, RevisionFactory, HelpfulVoteFactory


class KpiApiTests(TestCase):
    def _make_elastic_metric_kinds(self):
        click_kind = MetricKindFactory(code='search clickthroughs:elastic:clicks')
        search_kind = MetricKindFactory(code='search clickthroughs:elastic:searches')
        return click_kind, search_kind

    def _make_contributor_metric_kinds(self):
        MetricKindFactory(code=AOA_CONTRIBUTORS_METRIC_CODE)
        MetricKindFactory(code=KB_ENUS_CONTRIBUTORS_METRIC_CODE)
        MetricKindFactory(code=KB_L10N_CONTRIBUTORS_METRIC_CODE)
        MetricKindFactory(code=SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE)

    def _get_api_result(self, name, **kwargs):
        """Helper to make API calls, parse the json and return the result."""
        url = reverse(name)
        url = urlparams(url, format='json', **kwargs)
        response = self.client.get(url)
        eq_(200, response.status_code)
        return json.loads(response.content)

    def test_questions(self):
        """Test questions API call."""
        # A question with a solution:
        a = AnswerFactory()
        a.question.solution = a
        a.question.save()
        # A question with an answer:
        AnswerFactory()
        # A question without answers:
        QuestionFactory()
        # A locked question that shouldn't be counted for anything
        QuestionFactory(is_locked=True)

        r = self._get_api_result('api.kpi.questions')
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['responded_24'], 2)
        eq_(r['objects'][0]['responded_72'], 2)
        eq_(r['objects'][0]['questions'], 3)

    def test_questions_by_locale(self):
        """Test locale filtering of questions API call."""
        # An en-US question with a solution:
        q = QuestionFactory(locale='en-US')
        a = AnswerFactory(question=q)
        q.solution = a
        q.save()
        # An en-US question with an answer:
        q = QuestionFactory(locale='en-US')
        AnswerFactory(question=q)
        # An en-US question without answers:
        QuestionFactory(locale='en-US')

        # A pt-BR question without answers:
        QuestionFactory(locale='pt-BR')

        # Verify no locale filtering:
        r = self._get_api_result('api.kpi.questions')
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['responded_24'], 2)
        eq_(r['objects'][0]['responded_72'], 2)
        eq_(r['objects'][0]['questions'], 4)

        # Verify locale=en-US
        r = self._get_api_result('api.kpi.questions', locale='en-US')
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['responded_24'], 2)
        eq_(r['objects'][0]['responded_72'], 2)
        eq_(r['objects'][0]['questions'], 3)

        # Verify locale=pt-BR
        r = self._get_api_result('api.kpi.questions', locale='pt-BR')
        eq_(r['objects'][0]['questions'], 1)
        assert 'solved' not in r['objects'][0]
        assert 'responded_24' not in r['objects'][0]
        assert 'responded_72' not in r['objects'][0]

    def test_questions_by_product(self):
        """Test product filtering of questions API call."""
        firefox_os = ProductFactory(slug='firefox-os')
        firefox = ProductFactory(slug='firefox')

        # A Firefox OS question with a solution:
        q = QuestionFactory(product=firefox_os)
        a = AnswerFactory(question=q)
        q.solution = a
        q.save()

        # A Firefox OS question with an answer:
        q = QuestionFactory(product=firefox_os)
        AnswerFactory(question=q)

        # A Firefox OS question without answers:
        q = QuestionFactory(product=firefox_os)

        # A Firefox question without answers:
        q = QuestionFactory(product=firefox, locale='pt-BR')

        # Verify no product filtering:
        r = self._get_api_result('api.kpi.questions')
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['responded_24'], 2)
        eq_(r['objects'][0]['responded_72'], 2)
        eq_(r['objects'][0]['questions'], 4)

        # Verify product=firefox-os
        r = self._get_api_result('api.kpi.questions', product='firefox-os')
        eq_(r['objects'][0]['solved'], 1)
        eq_(r['objects'][0]['responded_24'], 2)
        eq_(r['objects'][0]['responded_72'], 2)
        eq_(r['objects'][0]['questions'], 3)

        # Verify product=firefox
        r = self._get_api_result('api.kpi.questions', product='firefox')
        eq_(r['objects'][0]['questions'], 1)
        assert 'solved' not in r['objects'][0]
        assert 'responded_24' not in r['objects'][0]
        assert 'responded_72' not in r['objects'][0]

    def test_questions_inactive_user(self):
        """Verify questions from inactive users aren't counted."""
        # Two questions for an inactive user.
        # They shouldn't show up in the count.
        u = UserFactory(is_active=False)
        QuestionFactory(creator=u)
        QuestionFactory(creator=u)

        r = self._get_api_result('api.kpi.questions')
        eq_(len(r['objects']), 0)

        # Activate the user, now the questions should count.
        u.is_active = True
        u.save()
        cache.clear()  # We need to clear the cache for new results.

        url = reverse('api.kpi.questions')
        response = self.client.get(url + '?format=json')
        eq_(200, response.status_code)
        r = json.loads(response.content)
        eq_(r['objects'][0]['questions'], 2)

    def test_vote(self):
        """Test vote API call."""
        r = RevisionFactory(is_approved=True)
        HelpfulVoteFactory(revision=r, helpful=False)
        HelpfulVoteFactory(revision=r, helpful=False)
        HelpfulVoteFactory(revision=r, helpful=True)

        a = AnswerFactory()
        AnswerVoteFactory(answer=a, helpful=False)
        AnswerVoteFactory(answer=a, helpful=True)
        AnswerVoteFactory(answer=a, helpful=True)

        r = self._get_api_result('api.kpi.votes')
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)
        eq_(r['objects'][0]['ans_helpful'], 2)
        eq_(r['objects'][0]['ans_votes'], 3)

    def test_kb_vote(self):
        """Test vote API call."""
        r1 = RevisionFactory(document__locale='en-US')
        r2 = RevisionFactory(document__locale='es')
        r3 = RevisionFactory(document__locale='es')
        for r in [r1, r2, r3]:
            HelpfulVoteFactory(revision=r)
            HelpfulVoteFactory(revision=r)
            HelpfulVoteFactory(revision=r, helpful=True)

        # Assign 2 documents to Firefox OS and 1 to Firefox
        firefox_os = ProductFactory(slug='firefox-os')
        firefox = ProductFactory(slug='firefox')
        r1.document.products.add(firefox_os)
        r2.document.products.add(firefox_os)
        r3.document.products.add(firefox)

        # All votes should be counted if we don't specify a locale
        r = self._get_api_result('api.kpi.kb-votes')
        eq_(r['objects'][0]['kb_helpful'], 3)
        eq_(r['objects'][0]['kb_votes'], 9)

        # Only en-US votes:
        r = self._get_api_result('api.kpi.kb-votes', locale='en-US')
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)

        # Only es votes:
        r = self._get_api_result('api.kpi.kb-votes', locale='es')
        eq_(r['objects'][0]['kb_helpful'], 2)
        eq_(r['objects'][0]['kb_votes'], 6)

        # Only Firefox OS votes:
        r = self._get_api_result('api.kpi.kb-votes', product='firefox-os')
        eq_(r['objects'][0]['kb_helpful'], 2)
        eq_(r['objects'][0]['kb_votes'], 6)

        # Only Firefox votes:
        r = self._get_api_result('api.kpi.kb-votes', product='firefox')
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)

        # Only Firefox OS + es votes:
        r = self._get_api_result(
            'api.kpi.kb-votes', product='firefox-os', locale='es')
        eq_(r['objects'][0]['kb_helpful'], 1)
        eq_(r['objects'][0]['kb_votes'], 3)

    def test_active_contributors(self):
        """Test active contributors API call."""
        # 2 en-US revisions by 2 contributors:
        r1 = RevisionFactory()
        r2 = RevisionFactory()
        # A translation with 2 contributors (translator + reviewer):
        d = DocumentFactory(parent=r1.document, locale='es')
        RevisionFactory(
            document=d,
            reviewed=datetime.now(),
            reviewer=r1.creator,
            creator=r2.creator)
        # 1 active support forum contributor:
        # A user with 10 answers
        u1 = UserFactory()
        for x in range(10):
            AnswerFactory(creator=u1)
        # A user with 9 answers
        u2 = UserFactory()
        # FIXME: create_batch?
        for x in range(9):
            AnswerFactory(creator=u2)
        # A user with 1 answer
        u3 = UserFactory()
        AnswerFactory(creator=u3)

        # An AoA reply (1 contributor):
        ReplyFactory()

        # Create metric kinds and update metrics for tomorrow (today's
        # activity shows up tomorrow).
        self._make_contributor_metric_kinds()
        update_contributor_metrics(day=date.today() + timedelta(days=1))

        r = self._get_api_result('api.kpi.contributors')

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
        q = QuestionFactory()
        u = q.creator
        AnswerFactory.create_batch(10, creator=u, question=q)

        # Create metric kinds and update metrics for tomorrow (today's
        # activity shows up tomorrow).
        self._make_contributor_metric_kinds()
        update_contributor_metrics(day=date.today() + timedelta(days=1))

        r = self._get_api_result('api.kpi.contributors')
        eq_(r['objects'][0]['support_forum'], 0)

        # Change the question creator, now we should have 1 contributor.
        q.creator = UserFactory()
        q.save()
        cache.clear()  # We need to clear the cache for new results.

        Metric.objects.all().delete()
        update_contributor_metrics(day=date.today() + timedelta(days=1))

        r = self._get_api_result('api.kpi.contributors')
        eq_(r['objects'][0]['support_forum'], 1)

    def test_elastic_clickthrough_get(self):
        """Test elastic clickthrough read API."""
        click_kind, search_kind = self._make_elastic_metric_kinds()
        MetricFactory(kind=click_kind, start=date(2000, 1, 1), value=1)
        MetricFactory(kind=search_kind, start=date(2000, 1, 1), value=10)
        MetricFactory(kind=click_kind, start=date(2000, 1, 9), value=2)
        MetricFactory(kind=search_kind, start=date(2000, 1, 9), value=20)

        url = reverse('api.kpi.search-ctr')
        response = self.client.get(url + '?format=json')
        data = json.loads(response.content)
        eq_(data['objects'], [
            {'clicks': 2, 'searches': 20,
             'start': u'2000-01-09'},
            {'clicks': 1, 'searches': 10,
             'start': u'2000-01-01'}])

        # Test filtering by start date:
        response = self.client.get(url + '?format=json&min_start=2000-01-09')
        data = json.loads(response.content)
        eq_(data['objects'], [{u'searches': 20, u'start': u'2000-01-09',
                               u'clicks': 2}])

    def test_visitors(self):
        """Test unique visitors API call."""
        # Create the metric.
        kind = MetricKindFactory(code=VISITORS_METRIC_CODE)
        MetricFactory(kind=kind, start=date.today(), end=date.today(), value=42)

        # There should be 42 visitors.
        r = self._get_api_result('api.kpi.visitors')
        eq_(r['objects'][0]['visitors'], 42)

    def test_l10n_coverage(self):
        """Test l10n coverage API call."""
        # Create the metrics
        kind = MetricKindFactory(code=L10N_METRIC_CODE)
        MetricFactory(kind=kind, start=date.today(), end=date.today(), value=56)

        # The l10n coverage should be 56%.
        r = self._get_api_result('api.kpi.l10n-coverage')
        eq_(r['objects'][0]['coverage'], 56)

    def test_exit_survey_results(self):
        """Test the exist survey results API call."""
        # Create the metrics
        kind = MetricKindFactory(code=EXIT_SURVEY_YES_CODE)
        MetricFactory(kind=kind, start=date.today(), end=date.today(), value=1337)
        kind = MetricKindFactory(code=EXIT_SURVEY_NO_CODE)
        MetricFactory(kind=kind, start=date.today(), end=date.today(), value=42)
        kind = MetricKindFactory(code=EXIT_SURVEY_DONT_KNOW_CODE)
        MetricFactory(kind=kind, start=date.today(), end=date.today(), value=777)

        # Verify the results returned from the API
        r = self._get_api_result('api.kpi.exit-survey')
        eq_(r['objects'][0]['yes'], 1337)
        eq_(r['objects'][0]['no'], 42)
        eq_(r['objects'][0]['dont_know'], 777)
