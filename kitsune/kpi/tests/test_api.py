import json
from datetime import date, datetime, timedelta

from django.core.cache import cache
from django.core.management import call_command

from kitsune.kpi.models import (
    EXIT_SURVEY_DONT_KNOW_CODE,
    EXIT_SURVEY_NO_CODE,
    EXIT_SURVEY_YES_CODE,
    KB_ENUS_CONTRIBUTORS_METRIC_CODE,
    KB_L10N_CONTRIBUTORS_METRIC_CODE,
    L10N_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE,
    VISITORS_METRIC_CODE,
    Metric,
)
from kitsune.kpi.tests import MetricFactory, MetricKindFactory
from kitsune.products.tests import ProductFactory
from kitsune.questions.tests import AnswerFactory, AnswerVoteFactory, QuestionFactory
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import DocumentFactory, HelpfulVoteFactory, RevisionFactory


class KpiApiTests(TestCase):
    def _make_elastic_metric_kinds(self):
        click_kind = MetricKindFactory(code="search clickthroughs:elastic:clicks")
        search_kind = MetricKindFactory(code="search clickthroughs:elastic:searches")
        return click_kind, search_kind

    def _make_contributor_metric_kinds(self):
        MetricKindFactory(code=KB_ENUS_CONTRIBUTORS_METRIC_CODE)
        MetricKindFactory(code=KB_L10N_CONTRIBUTORS_METRIC_CODE)
        MetricKindFactory(code=SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE)

    def _get_api_result(self, name, **kwargs):
        """Helper to make API calls, parse the json and return the result."""
        url = reverse(name)
        url = urlparams(url, format="json", **kwargs)
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        return json.loads(response.content)

    def test_questions(self):
        """Test questions API call."""
        # Create a question with a solution. Note that it's important, and
        # more realistic, to create the question prior to the answer, because
        # the "QuestionsMetricList" code checks for answers created within
        # periods of time from the creation of their questions.
        a = AnswerFactory(question=QuestionFactory())
        a.question.solution = a
        a.question.save()
        # Create a question with an answer.
        AnswerFactory(question=QuestionFactory())
        # Create a question without any answers.
        QuestionFactory()
        # Create a locked question that shouldn't be counted for anything.
        QuestionFactory(is_locked=True)

        r = self._get_api_result("api.kpi.questions")
        self.assertEqual(r["objects"][0]["solved"], 1)
        self.assertEqual(r["objects"][0]["responded_24"], 2)
        self.assertEqual(r["objects"][0]["responded_72"], 2)
        self.assertEqual(r["objects"][0]["questions"], 3)

    def test_questions_by_locale(self):
        """Test locale filtering of questions API call."""
        # An en-US question with a solution:
        q = QuestionFactory(locale="en-US")
        a = AnswerFactory(question=q)
        q.solution = a
        q.save()
        # An en-US question with an answer:
        q = QuestionFactory(locale="en-US")
        AnswerFactory(question=q)
        # An en-US question without answers:
        QuestionFactory(locale="en-US")

        # A pt-BR question without answers:
        QuestionFactory(locale="pt-BR")

        # Verify no locale filtering:
        r = self._get_api_result("api.kpi.questions")
        self.assertEqual(r["objects"][0]["solved"], 1)
        self.assertEqual(r["objects"][0]["responded_24"], 2)
        self.assertEqual(r["objects"][0]["responded_72"], 2)
        self.assertEqual(r["objects"][0]["questions"], 4)

        # Verify locale=en-US
        r = self._get_api_result("api.kpi.questions", locale="en-US")
        self.assertEqual(r["objects"][0]["solved"], 1)
        self.assertEqual(r["objects"][0]["responded_24"], 2)
        self.assertEqual(r["objects"][0]["responded_72"], 2)
        self.assertEqual(r["objects"][0]["questions"], 3)

        # Verify locale=pt-BR
        r = self._get_api_result("api.kpi.questions", locale="pt-BR")
        self.assertEqual(r["objects"][0]["questions"], 1)
        assert "solved" not in r["objects"][0]
        assert "responded_24" not in r["objects"][0]
        assert "responded_72" not in r["objects"][0]

    def test_questions_by_product(self):
        """Test product filtering of questions API call."""
        firefox_os = ProductFactory(slug="firefox-os")
        firefox = ProductFactory(slug="firefox")

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
        q = QuestionFactory(product=firefox, locale="pt-BR")

        # Verify no product filtering:
        r = self._get_api_result("api.kpi.questions")
        self.assertEqual(r["objects"][0]["solved"], 1)
        self.assertEqual(r["objects"][0]["responded_24"], 2)
        self.assertEqual(r["objects"][0]["responded_72"], 2)
        self.assertEqual(r["objects"][0]["questions"], 4)

        # Verify product=firefox-os
        r = self._get_api_result("api.kpi.questions", product="firefox-os")
        self.assertEqual(r["objects"][0]["solved"], 1)
        self.assertEqual(r["objects"][0]["responded_24"], 2)
        self.assertEqual(r["objects"][0]["responded_72"], 2)
        self.assertEqual(r["objects"][0]["questions"], 3)

        # Verify product=firefox
        r = self._get_api_result("api.kpi.questions", product="firefox")
        self.assertEqual(r["objects"][0]["questions"], 1)
        assert "solved" not in r["objects"][0]
        assert "responded_24" not in r["objects"][0]
        assert "responded_72" not in r["objects"][0]

    def test_questions_inactive_user(self):
        """Verify questions from inactive users aren't counted."""
        # Two questions for an inactive user.
        # They shouldn't show up in the count.
        u = UserFactory(is_active=False)
        QuestionFactory(creator=u)
        QuestionFactory(creator=u)

        r = self._get_api_result("api.kpi.questions")
        self.assertEqual(len(r["objects"]), 0)

        # Activate the user, now the questions should count.
        u.is_active = True
        u.save()
        cache.clear()  # We need to clear the cache for new results.

        url = reverse("api.kpi.questions")
        response = self.client.get(url + "?format=json")
        self.assertEqual(200, response.status_code)
        r = json.loads(response.content)
        self.assertEqual(r["objects"][0]["questions"], 2)

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

        r = self._get_api_result("api.kpi.votes")
        self.assertEqual(r["objects"][0]["kb_helpful"], 1)
        self.assertEqual(r["objects"][0]["kb_votes"], 3)
        self.assertEqual(r["objects"][0]["ans_helpful"], 2)
        self.assertEqual(r["objects"][0]["ans_votes"], 3)

    def test_kb_vote(self):
        """Test vote API call."""
        r1 = RevisionFactory(document__locale="en-US")
        r2 = RevisionFactory(document__locale="es")
        r3 = RevisionFactory(document__locale="es")
        for r in [r1, r2, r3]:
            HelpfulVoteFactory(revision=r)
            HelpfulVoteFactory(revision=r)
            HelpfulVoteFactory(revision=r, helpful=True)

        # Assign 2 documents to Firefox OS and 1 to Firefox
        firefox_os = ProductFactory(slug="firefox-os")
        firefox = ProductFactory(slug="firefox")
        r1.document.products.add(firefox_os)
        r2.document.products.add(firefox_os)
        r3.document.products.add(firefox)

        # All votes should be counted if we don't specify a locale
        r = self._get_api_result("api.kpi.kb-votes")
        self.assertEqual(r["objects"][0]["kb_helpful"], 3)
        self.assertEqual(r["objects"][0]["kb_votes"], 9)

        # Only en-US votes:
        r = self._get_api_result("api.kpi.kb-votes", locale="en-US")
        self.assertEqual(r["objects"][0]["kb_helpful"], 1)
        self.assertEqual(r["objects"][0]["kb_votes"], 3)

        # Only es votes:
        r = self._get_api_result("api.kpi.kb-votes", locale="es")
        self.assertEqual(r["objects"][0]["kb_helpful"], 2)
        self.assertEqual(r["objects"][0]["kb_votes"], 6)

        # Only Firefox OS votes:
        r = self._get_api_result("api.kpi.kb-votes", product="firefox-os")
        self.assertEqual(r["objects"][0]["kb_helpful"], 2)
        self.assertEqual(r["objects"][0]["kb_votes"], 6)

        # Only Firefox votes:
        r = self._get_api_result("api.kpi.kb-votes", product="firefox")
        self.assertEqual(r["objects"][0]["kb_helpful"], 1)
        self.assertEqual(r["objects"][0]["kb_votes"], 3)

        # Only Firefox OS + es votes:
        r = self._get_api_result("api.kpi.kb-votes", product="firefox-os", locale="es")
        self.assertEqual(r["objects"][0]["kb_helpful"], 1)
        self.assertEqual(r["objects"][0]["kb_votes"], 3)

    def test_active_contributors(self):
        """Test active contributors API call."""
        # 2 en-US revisions by 2 contributors:
        r1 = RevisionFactory()
        r2 = RevisionFactory()
        # A translation with 2 contributors (translator + reviewer):
        d = DocumentFactory(parent=r1.document, locale="es")
        RevisionFactory(
            document=d, reviewed=datetime.now(), reviewer=r1.creator, creator=r2.creator
        )
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

        # Create metric kinds and update metrics for tomorrow (today's
        # activity shows up tomorrow).
        self._make_contributor_metric_kinds()
        call_command("update_contributor_metrics", str(date.today() + timedelta(days=1)))

        r = self._get_api_result("api.kpi.contributors")

        self.assertEqual(r["objects"][0]["en_us"], 2)
        self.assertEqual(r["objects"][0]["non_en_us"], 2)
        self.assertEqual(r["objects"][0]["support_forum"], 1)

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
        call_command("update_contributor_metrics", str(date.today() + timedelta(days=1)))

        r = self._get_api_result("api.kpi.contributors")
        self.assertEqual(r["objects"][0]["support_forum"], 0)

        # Change the question creator, now we should have 1 contributor.
        q.creator = UserFactory()
        q.save()
        cache.clear()  # We need to clear the cache for new results.

        Metric.objects.all().delete()
        call_command("update_contributor_metrics", str(date.today() + timedelta(days=1)))

        r = self._get_api_result("api.kpi.contributors")
        self.assertEqual(r["objects"][0]["support_forum"], 1)

    def test_elastic_clickthrough_get(self):
        """Test elastic clickthrough read API."""
        click_kind, search_kind = self._make_elastic_metric_kinds()
        MetricFactory(kind=click_kind, start=date(2000, 1, 1), value=1)
        MetricFactory(kind=search_kind, start=date(2000, 1, 1), value=10)
        MetricFactory(kind=click_kind, start=date(2000, 1, 9), value=2)
        MetricFactory(kind=search_kind, start=date(2000, 1, 9), value=20)

        url = reverse("api.kpi.search-ctr")
        response = self.client.get(url + "?format=json")
        data = json.loads(response.content)
        self.assertEqual(
            data["objects"],
            [
                {"clicks": 2, "searches": 20, "start": "2000-01-09"},
                {"clicks": 1, "searches": 10, "start": "2000-01-01"},
            ],
        )

        # Test filtering by start date:
        response = self.client.get(url + "?format=json&min_start=2000-01-09")
        data = json.loads(response.content)
        self.assertEqual(data["objects"], [{"searches": 20, "start": "2000-01-09", "clicks": 2}])

    def test_visitors(self):
        """Test unique visitors API call."""
        # Create the metric.
        kind = MetricKindFactory(code=VISITORS_METRIC_CODE)
        MetricFactory(kind=kind, start=date.today(), end=date.today(), value=42)

        # There should be 42 visitors.
        r = self._get_api_result("api.kpi.visitors")
        self.assertEqual(r["objects"][0]["visitors"], 42)

    def test_l10n_coverage(self):
        """Test l10n coverage API call."""
        # Create the metrics
        kind = MetricKindFactory(code=L10N_METRIC_CODE)
        MetricFactory(kind=kind, start=date.today(), end=date.today(), value=56)

        # The l10n coverage should be 56%.
        r = self._get_api_result("api.kpi.l10n-coverage")
        self.assertEqual(r["objects"][0]["coverage"], 56)

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
        r = self._get_api_result("api.kpi.exit-survey")
        self.assertEqual(r["objects"][0]["yes"], 1337)
        self.assertEqual(r["objects"][0]["no"], 42)
        self.assertEqual(r["objects"][0]["dont_know"], 777)
