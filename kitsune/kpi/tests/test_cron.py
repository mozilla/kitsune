from datetime import date, datetime, timedelta
from unittest.mock import patch

from django.core.management import call_command

import kitsune.kpi.management.utils
from kitsune.kpi.models import (
    CONTRIBUTOR_COHORT_CODE,
    KB_ENUS_CONTRIBUTOR_COHORT_CODE,
    KB_L10N_CONTRIBUTOR_COHORT_CODE,
    L10N_METRIC_CODE,
    SEARCH_CLICKS_METRIC_CODE,
    SEARCH_SEARCHES_METRIC_CODE,
    SUPPORT_FORUM_HELPER_COHORT_CODE,
    VISITORS_METRIC_CODE,
    Cohort,
    Metric,
)
from kitsune.kpi.tasks import cohort_analysis, update_l10n_metric
from kitsune.kpi.tests import MetricFactory, MetricKindFactory
from kitsune.questions.tests import AnswerFactory
from kitsune.sumo import googleanalytics
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.config import MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE
from kitsune.wiki.tests import ApprovedRevisionFactory, DocumentFactory


class CohortAnalysisTests(TestCase):
    def setUp(self):
        today = datetime.today()
        self.start_of_first_week = today - timedelta(days=today.weekday(), weeks=12)

        revisions = ApprovedRevisionFactory.create_batch(3, created=self.start_of_first_week)

        reviewer = UserFactory()
        ApprovedRevisionFactory(reviewer=reviewer, created=self.start_of_first_week)

        ApprovedRevisionFactory(
            creator=revisions[1].creator,
            reviewer=reviewer,
            created=self.start_of_first_week + timedelta(weeks=1, days=2),
        )
        ApprovedRevisionFactory(created=self.start_of_first_week + timedelta(weeks=1, days=1))

        for r in revisions:
            lr = ApprovedRevisionFactory(
                created=self.start_of_first_week + timedelta(days=1), document__locale="es"
            )
            ApprovedRevisionFactory(
                created=self.start_of_first_week + timedelta(weeks=2, days=1),
                creator=lr.creator,
                document__locale="es",
            )

        answers = AnswerFactory.create_batch(
            7, created=self.start_of_first_week + timedelta(weeks=1, days=2)
        )

        AnswerFactory(
            question=answers[2].question,
            creator=answers[2].question.creator,
            created=self.start_of_first_week + timedelta(weeks=1, days=2),
        )

        for a in answers[:2]:
            AnswerFactory(
                creator=a.creator, created=self.start_of_first_week + timedelta(weeks=2, days=5)
            )

        cohort_analysis()

    def test_contributor_cohort_analysis(self):
        c1 = Cohort.objects.get(kind__code=CONTRIBUTOR_COHORT_CODE, start=self.start_of_first_week)
        self.assertEqual(c1.size, 8)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        self.assertEqual(c1r1.size, 2)

        c1r2 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))
        self.assertEqual(c1r2.size, 3)

        c2 = Cohort.objects.get(
            kind__code=CONTRIBUTOR_COHORT_CODE, start=self.start_of_first_week + timedelta(weeks=1)
        )
        self.assertEqual(c2.size, 8)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        self.assertEqual(c2r1.size, 2)

    def test_kb_enus_contributor_cohort_analysis(self):
        c1 = Cohort.objects.get(
            kind__code=KB_ENUS_CONTRIBUTOR_COHORT_CODE, start=self.start_of_first_week
        )
        self.assertEqual(c1.size, 5)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        self.assertEqual(c1r1.size, 2)

        c1r2 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))
        self.assertEqual(c1r2.size, 0)

        c2 = Cohort.objects.get(
            kind__code=KB_ENUS_CONTRIBUTOR_COHORT_CODE,
            start=self.start_of_first_week + timedelta(weeks=1),
        )
        self.assertEqual(c2.size, 1)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        self.assertEqual(c2r1.size, 0)

    def test_kb_l10n_contributor_cohort_analysis(self):
        c1 = Cohort.objects.get(
            kind__code=KB_L10N_CONTRIBUTOR_COHORT_CODE, start=self.start_of_first_week
        )
        self.assertEqual(c1.size, 3)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        self.assertEqual(c1r1.size, 0)

        c1r2 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))
        self.assertEqual(c1r2.size, 3)

        c2 = Cohort.objects.get(
            kind__code=KB_L10N_CONTRIBUTOR_COHORT_CODE,
            start=self.start_of_first_week + timedelta(weeks=1),
        )
        self.assertEqual(c2.size, 0)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        self.assertEqual(c2r1.size, 0)

    def test_support_forum_helper_cohort_analysis(self):
        c1 = Cohort.objects.get(
            kind__code=SUPPORT_FORUM_HELPER_COHORT_CODE, start=self.start_of_first_week
        )
        self.assertEqual(c1.size, 0)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        self.assertEqual(c1r1.size, 0)

        c2 = Cohort.objects.get(
            kind__code=SUPPORT_FORUM_HELPER_COHORT_CODE,
            start=self.start_of_first_week + timedelta(weeks=1),
        )
        self.assertEqual(c2.size, 7)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        self.assertEqual(c2r1.size, 2)


class CronJobTests(TestCase):
    @patch.object(googleanalytics, "visitors")
    def test_update_visitors_cron(self, visitors):
        """Verify the cron job inserts the right rows."""
        visitor_kind = MetricKindFactory(code=VISITORS_METRIC_CODE)

        today = date.today()
        days_ago_4 = today - timedelta(days=4)
        days_ago_3 = today - timedelta(days=3)
        days_ago_2 = today - timedelta(days=2)
        days_ago_1 = today - timedelta(days=1)

        MetricFactory(start=days_ago_4, end=days_ago_3, kind=visitor_kind, value=200)

        visitors.return_value = (
            row
            for row in (
                (days_ago_3, 42),
                (days_ago_2, 193),
                (days_ago_1, 33),
            )
        )

        call_command("update_visitors_metric")

        metrics = Metric.objects.filter(kind=visitor_kind).order_by("start")
        self.assertEqual(4, len(metrics))
        self.assertEqual(200, metrics[0].value)
        self.assertEqual(days_ago_4, metrics[0].start)
        self.assertEqual(42, metrics[1].value)
        self.assertEqual(days_ago_3, metrics[1].start)
        self.assertEqual(193, metrics[2].value)
        self.assertEqual(days_ago_2, metrics[2].start)
        self.assertEqual(33, metrics[3].value)
        self.assertEqual(days_ago_1, metrics[3].start)

    @patch.object(kitsune.kpi.management.utils, "_get_top_docs")
    @patch.object(googleanalytics, "visitors_by_locale")
    def test_update_l10n_metric_cron(self, visitors_by_locale, _get_top_docs):
        """Verify the cron job creates the correct metric."""
        l10n_kind = MetricKindFactory(code=L10N_METRIC_CODE)

        # Create the en-US document with an approved revision.
        doc = DocumentFactory()
        rev = ApprovedRevisionFactory(
            document=doc, significance=MEDIUM_SIGNIFICANCE, is_ready_for_localization=True
        )

        # Create an es translation that is up to date.
        es_doc = DocumentFactory(parent=doc, locale="es")
        ApprovedRevisionFactory(document=es_doc, based_on=rev)

        # Create a de translation without revisions.
        DocumentFactory(parent=doc, locale="de")

        # Mock some calls.
        visitors_by_locale.return_value = {
            "en-US": 50,
            "de": 20,
            "es": 25,
            "fr": 5,
        }
        _get_top_docs.return_value = [doc]

        # Run it and verify results.
        # Value should be 75% (1/1 * 25/100 + 1/1 * 50/100)
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        self.assertEqual(1, len(metrics))
        self.assertEqual(75, metrics[0].value)

        # Create a new revision with TYPO_SIGNIFICANCE. It shouldn't
        # affect the results.
        ApprovedRevisionFactory(
            document=doc, significance=TYPO_SIGNIFICANCE, is_ready_for_localization=True
        )
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        self.assertEqual(1, len(metrics))
        self.assertEqual(75, metrics[0].value)

        # Create a new revision with MEDIUM_SIGNIFICANCE. The coverage
        # should now be 62% (0.5/1 * 25/100 + 1/1 * 50/100)
        m1 = ApprovedRevisionFactory(
            document=doc, significance=MEDIUM_SIGNIFICANCE, is_ready_for_localization=True
        )
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        self.assertEqual(1, len(metrics))
        self.assertEqual(62, metrics[0].value)

        # And another new revision with MEDIUM_SIGNIFICANCE makes the
        # coverage 50% (1/1 * 50/100).
        m2 = ApprovedRevisionFactory(
            document=doc, significance=MEDIUM_SIGNIFICANCE, is_ready_for_localization=True
        )
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        self.assertEqual(1, len(metrics))
        self.assertEqual(50, metrics[0].value)

        # If we remove the two MEDIUM_SIGNIFICANCE revisions and add a
        # MAJOR_SIGNIFICANCE revision, the coverage is 50% as well.
        ApprovedRevisionFactory(
            document=doc, significance=MAJOR_SIGNIFICANCE, is_ready_for_localization=True
        )
        m1.delete()
        m2.delete()
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        self.assertEqual(1, len(metrics))
        self.assertEqual(50, metrics[0].value)

    @patch.object(googleanalytics, "search_clicks_and_impressions")
    def test_update_search_ctr(self, search_clicks_and_impressions):
        """Verify the cron job inserts the right rows."""
        clicks_kind = MetricKindFactory(code=SEARCH_CLICKS_METRIC_CODE)
        searches_kind = MetricKindFactory(code=SEARCH_SEARCHES_METRIC_CODE)

        today = date.today()
        days_ago_4 = today - timedelta(days=4)
        days_ago_3 = today - timedelta(days=3)
        days_ago_2 = today - timedelta(days=2)
        days_ago_1 = today - timedelta(days=1)

        MetricFactory(start=days_ago_4, end=days_ago_3, kind=clicks_kind, value=100)
        MetricFactory(start=days_ago_4, end=days_ago_3, kind=searches_kind, value=200)

        search_clicks_and_impressions.return_value = (
            row
            for row in (
                (days_ago_3, 177, 421),
                (days_ago_2, 19, 138),
                (days_ago_1, 990, 995),
            )
        )

        call_command("update_search_ctr_metric")

        clicks_metrics = Metric.objects.filter(kind=clicks_kind).order_by("start")
        self.assertEqual(4, len(clicks_metrics))
        self.assertEqual(100, clicks_metrics[0].value)
        self.assertEqual(days_ago_4, clicks_metrics[0].start)
        self.assertEqual(177, clicks_metrics[1].value)
        self.assertEqual(days_ago_3, clicks_metrics[1].start)
        self.assertEqual(19, clicks_metrics[2].value)
        self.assertEqual(days_ago_2, clicks_metrics[2].start)
        self.assertEqual(990, clicks_metrics[3].value)
        self.assertEqual(days_ago_1, clicks_metrics[3].start)

        searches_metrics = Metric.objects.filter(kind=searches_kind).order_by("start")
        self.assertEqual(4, len(searches_metrics))
        self.assertEqual(200, searches_metrics[0].value)
        self.assertEqual(days_ago_4, searches_metrics[0].start)
        self.assertEqual(421, searches_metrics[1].value)
        self.assertEqual(days_ago_3, searches_metrics[1].start)
        self.assertEqual(138, searches_metrics[2].value)
        self.assertEqual(days_ago_2, searches_metrics[2].start)
        self.assertEqual(995, searches_metrics[3].value)
        self.assertEqual(days_ago_1, searches_metrics[3].start)
