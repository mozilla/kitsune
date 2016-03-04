from datetime import date, datetime, timedelta

from mock import patch
from nose.tools import eq_

import kitsune.kpi.cron
from kitsune.customercare.tests import ReplyFactory
from kitsune.kpi import surveygizmo_utils
from kitsune.kpi.cron import (
    cohort_analysis, update_visitors_metric, update_l10n_metric, googleanalytics,
    update_search_ctr_metric, _process_exit_survey_results)
from kitsune.kpi.models import (
    Metric, Cohort, VISITORS_METRIC_CODE, L10N_METRIC_CODE, SEARCH_CLICKS_METRIC_CODE,
    SEARCH_SEARCHES_METRIC_CODE, EXIT_SURVEY_YES_CODE, EXIT_SURVEY_NO_CODE,
    EXIT_SURVEY_DONT_KNOW_CODE, CONTRIBUTOR_COHORT_CODE, KB_ENUS_CONTRIBUTOR_COHORT_CODE,
    KB_L10N_CONTRIBUTOR_COHORT_CODE, SUPPORT_FORUM_HELPER_COHORT_CODE, AOA_CONTRIBUTOR_COHORT_CODE)
from kitsune.kpi.tests import MetricKindFactory, MetricFactory
from kitsune.questions.tests import AnswerFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.config import (
    MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE)
from kitsune.wiki.tests import DocumentFactory, ApprovedRevisionFactory


class CohortAnalysisTests(TestCase):
    def setUp(self):
        today = datetime.today()
        self.start_of_first_week = today - timedelta(days=today.weekday(), weeks=12)

        revisions = ApprovedRevisionFactory.create_batch(3, created=self.start_of_first_week)

        reviewer = UserFactory()
        ApprovedRevisionFactory(reviewer=reviewer, created=self.start_of_first_week)

        ApprovedRevisionFactory(creator=revisions[1].creator, reviewer=reviewer,
                                created=self.start_of_first_week + timedelta(weeks=1, days=2))
        ApprovedRevisionFactory(created=self.start_of_first_week + timedelta(weeks=1, days=1))

        for r in revisions:
            lr = ApprovedRevisionFactory(created=self.start_of_first_week + timedelta(days=1),
                                         document__locale='es')
            ApprovedRevisionFactory(created=self.start_of_first_week + timedelta(weeks=2, days=1),
                                    creator=lr.creator, document__locale='es')

        answers = AnswerFactory.create_batch(
            7, created=self.start_of_first_week + timedelta(weeks=1, days=2))

        AnswerFactory(question=answers[2].question, creator=answers[2].question.creator,
                      created=self.start_of_first_week + timedelta(weeks=1, days=2))

        for a in answers[:2]:
            AnswerFactory(creator=a.creator,
                          created=self.start_of_first_week + timedelta(weeks=2, days=5))

        replies = ReplyFactory.create_batch(2, created=self.start_of_first_week)

        for r in replies:
            ReplyFactory(user=r.user, created=self.start_of_first_week + timedelta(weeks=2))

        cohort_analysis()

    def test_contributor_cohort_analysis(self):
        c1 = Cohort.objects.get(kind__code=CONTRIBUTOR_COHORT_CODE, start=self.start_of_first_week)
        eq_(c1.size, 10)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c1r1.size, 2)

        c1r2 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))
        eq_(c1r2.size, 5)

        c2 = Cohort.objects.get(kind__code=CONTRIBUTOR_COHORT_CODE,
                                start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c2.size, 8)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        eq_(c2r1.size, 2)

    def test_kb_enus_contributor_cohort_analysis(self):
        c1 = Cohort.objects.get(kind__code=KB_ENUS_CONTRIBUTOR_COHORT_CODE,
                                start=self.start_of_first_week)
        eq_(c1.size, 5)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c1r1.size, 2)

        c1r2 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))
        eq_(c1r2.size, 0)

        c2 = Cohort.objects.get(kind__code=KB_ENUS_CONTRIBUTOR_COHORT_CODE,
                                start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c2.size, 1)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        eq_(c2r1.size, 0)

    def test_kb_l10n_contributor_cohort_analysis(self):
        c1 = Cohort.objects.get(kind__code=KB_L10N_CONTRIBUTOR_COHORT_CODE,
                                start=self.start_of_first_week)
        eq_(c1.size, 3)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c1r1.size, 0)

        c1r2 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))
        eq_(c1r2.size, 3)

        c2 = Cohort.objects.get(kind__code=KB_L10N_CONTRIBUTOR_COHORT_CODE,
                                start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c2.size, 0)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        eq_(c2r1.size, 0)

    def test_support_forum_helper_cohort_analysis(self):
        c1 = Cohort.objects.get(kind__code=SUPPORT_FORUM_HELPER_COHORT_CODE,
                                start=self.start_of_first_week)
        eq_(c1.size, 0)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c1r1.size, 0)

        c2 = Cohort.objects.get(kind__code=SUPPORT_FORUM_HELPER_COHORT_CODE,
                                start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c2.size, 7)

        c2r1 = c2.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))

        eq_(c2r1.size, 2)

    def test_aoa_contributor_cohort_analysis(self):
        c1 = Cohort.objects.get(kind__code=AOA_CONTRIBUTOR_COHORT_CODE,
                                start=self.start_of_first_week)
        eq_(c1.size, 2)

        c1r1 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c1r1.size, 0)

        c1r2 = c1.retention_metrics.get(start=self.start_of_first_week + timedelta(weeks=2))
        eq_(c1r2.size, 2)

        c2 = Cohort.objects.get(kind__code=AOA_CONTRIBUTOR_COHORT_CODE,
                                start=self.start_of_first_week + timedelta(weeks=1))
        eq_(c2.size, 0)


class CronJobTests(TestCase):
    @patch.object(googleanalytics, 'visitors')
    def test_update_visitors_cron(self, visitors):
        """Verify the cron job inserts the right rows."""
        visitor_kind = MetricKindFactory(code=VISITORS_METRIC_CODE)
        visitors.return_value = {'2012-01-13': 42,
                                 '2012-01-14': 193,
                                 '2012-01-15': 33}

        update_visitors_metric()

        metrics = Metric.objects.filter(kind=visitor_kind).order_by('start')
        eq_(3, len(metrics))
        eq_(42, metrics[0].value)
        eq_(193, metrics[1].value)
        eq_(date(2012, 1, 15), metrics[2].start)

    @patch.object(kitsune.kpi.cron, '_get_top_docs')
    @patch.object(googleanalytics, 'visitors_by_locale')
    def test_update_l10n_metric_cron(self, visitors_by_locale, _get_top_docs):
        """Verify the cron job creates the correct metric."""
        l10n_kind = MetricKindFactory(code=L10N_METRIC_CODE)

        # Create the en-US document with an approved revision.
        doc = DocumentFactory()
        rev = ApprovedRevisionFactory(
            document=doc,
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True)

        # Create an es translation that is up to date.
        es_doc = DocumentFactory(parent=doc, locale='es')
        ApprovedRevisionFactory(document=es_doc, based_on=rev)

        # Create a de translation without revisions.
        DocumentFactory(parent=doc, locale='de')

        # Mock some calls.
        visitors_by_locale.return_value = {
            'en-US': 50,
            'de': 20,
            'es': 25,
            'fr': 5,
        }
        _get_top_docs.return_value = [doc]

        # Run it and verify results.
        # Value should be 75% (1/1 * 25/100 + 1/1 * 50/100)
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(75, metrics[0].value)

        # Create a new revision with TYPO_SIGNIFICANCE. It shouldn't
        # affect the results.
        ApprovedRevisionFactory(
            document=doc,
            significance=TYPO_SIGNIFICANCE,
            is_ready_for_localization=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(75, metrics[0].value)

        # Create a new revision with MEDIUM_SIGNIFICANCE. The coverage
        # should now be 62% (0.5/1 * 25/100 + 1/1 * 50/100)
        m1 = ApprovedRevisionFactory(
            document=doc,
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(62, metrics[0].value)

        # And another new revision with MEDIUM_SIGNIFICANCE makes the
        # coverage 50% (1/1 * 50/100).
        m2 = ApprovedRevisionFactory(
            document=doc,
            significance=MEDIUM_SIGNIFICANCE,
            is_ready_for_localization=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(50, metrics[0].value)

        # If we remove the two MEDIUM_SIGNIFICANCE revisions and add a
        # MAJOR_SIGNIFICANCE revision, the coverage is 50% as well.
        m1.delete()
        m2.delete()
        ApprovedRevisionFactory(
            document=doc,
            significance=MAJOR_SIGNIFICANCE,
            is_ready_for_localization=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(50, metrics[0].value)

    @patch.object(googleanalytics, 'search_ctr')
    def test_update_search_ctr(self, search_ctr):
        """Verify the cron job inserts the right rows."""
        clicks_kind = MetricKindFactory(code=SEARCH_CLICKS_METRIC_CODE)
        MetricKindFactory(code=SEARCH_SEARCHES_METRIC_CODE)
        search_ctr.return_value = {'2013-06-06': 42.123456789,
                                   '2013-06-07': 13.7654321,
                                   '2013-06-08': 99.55555}

        update_search_ctr_metric()

        metrics = Metric.objects.filter(kind=clicks_kind).order_by('start')
        eq_(3, len(metrics))
        eq_(421, metrics[0].value)
        eq_(138, metrics[1].value)
        eq_(date(2013, 6, 8), metrics[2].start)

    @patch.object(surveygizmo_utils, 'requests')
    def test_process_exit_surveys(self, requests):
        """Verify the metrics inserted by process_exit_surveys cron job."""
        requests.get.return_value.content = SURVEY_GIZMO_EXIT_SURVEY_RESPONSE

        # Create the kinds.
        yes_kind = MetricKindFactory(code=EXIT_SURVEY_YES_CODE)
        no_kind = MetricKindFactory(code=EXIT_SURVEY_NO_CODE)
        dunno_kind = MetricKindFactory(code=EXIT_SURVEY_DONT_KNOW_CODE)
        two_days_back = date.today() - timedelta(days=2)

        # Add a metric for 2 days ago so only 1 new day is collected.
        MetricFactory(kind=yes_kind, start=two_days_back)

        # Collect and process.
        with self.settings(SURVEYGIZMO_API_TOKEN='test',
                           SURVEYGIZMO_API_TOKEN_SECRET='test'):
            _process_exit_survey_results()

        # Verify.
        eq_(4, Metric.objects.count())
        eq_(2, Metric.objects.filter(kind=yes_kind)[1].value)
        eq_(1, Metric.objects.get(kind=no_kind).value)
        eq_(1, Metric.objects.get(kind=dunno_kind).value)


SURVEY_GIZMO_EXIT_SURVEY_RESPONSE = """
{
    "total_count": "4",
    "total_pages": 1,
    "results_per_page": "500",
    "result_ok": true,
    "data": [
        {
            "[variable(\\"8-shown\\")]": "1",
            "[variable(\\"1-shown\\")]": "1",
            "[variable(\\"4-shown\\")]": "1",
            "[variable(\\"2-shown\\")]": "1",
            "[variable(\\"7-shown\\")]": "1",
            "contact_id": "100019965",
            "[variable(\\"STANDARD_USERAGENT\\")]": "Mozilla/5.0 (Windows NT 6\
.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/5\
37.36",
            "[question(6)]": "I most often use Chrome to browse because it has\
 a native omni bar, but I really like what you guys are doing and am hoping th\
at Firefox OS will be supported on my smartphone when it\'s released.",
            "[question(4)]": " 9\\r",
            "[variable(\\"STANDARD_GEOREGION\\")]": "00",
            "id": "3970",
            "[question(2)]": "Yes\\n",
            "[variable(\\"PORTAL_RELATIONSHIP\\")]": "",
            "[variable(\\"STANDARD_REFERER\\")]": "",
            "[variable(\\"STANDARD_RESPONSETIME\\")]": "",
            "sResponseComment": "",
            "datesubmitted": "2013-07-16 00:31:26",
            "[question(8)]": "Learn more about Firefox",
            "[variable(\\"STANDARD_COMMENTS\\")]": "",
            "[variable(\\"STANDARD_GEODMA\\")]": "0",
            "status": "Complete",
            "[variable(\\"6-shown\\")]": "1",
            "[variable(\\"STANDARD_LAT\\")]": "1.2931",
            "[variable(\\"STANDARD_GEOPOSTAL\\")]": "",
            "[question(3), option(10004)]": "Help Articles\\n",
            "[variable(\\"STANDARD_IP\\")]": "111.111.1.111, 111.111.11",
            "[variable(4)]": "10007",
            "is_test_data": "0",
            "[url(\\"_\\")]": "",
            "[variable(\\"STANDARD_GEOCITY\\")]": "Singapore",
            "[url(\\"sguid\\")]": "",
            "[variable(2)]": "10001",
            "[variable(\\"STANDARD_GEOCOUNTRY\\")]": "Singapore",
            "[variable(\\"3-shown\\")]": "1",
            "[question(3), option(10006)]": "",
            "[variable(\\"STANDARD_LONG\\")]": "103.855797",
            "[variable(8)]": "10018",
            "[question(3), option(10005)]": ""
        }, {
            "[variable(\\"8-shown\\")]": "1",
            "[variable(\\"1-shown\\")]": "1",
            "[variable(\\"4-shown\\")]": "1",
            "[variable(\\"2-shown\\")]": "1",
            "[variable(\\"7-shown\\")]": "1",
            "contact_id": "100020010",
            "[variable(\\"STANDARD_USERAGENT\\")]": "Mozilla/5.0 (Windows NT 5\
.1; rv:22.0) Gecko/20100101 Firefox/22.0",
            "[question(6)]": "i know  mozilla firefox has  very experienced te\
am what ever they are doing it is for the mankind and i can simply send best w\
ishes\\r\\nthanks  that u give honour to ordinary people like me",
            "[question(4)]": " 9\\r",
            "[variable(\\"STANDARD_GEOREGION\\")]": "35",
            "id": "3971",
            "[question(2)]": "No\\n",
            "[variable(\\"PORTAL_RELATIONSHIP\\")]": "",
            "[variable(\\"STANDARD_REFERER\\")]": "http://in-mg61.mail.yahoo.c\
om/neo/launch",
            "[variable(\\"STANDARD_RESPONSETIME\\")]": "",
            "sResponseComment": "",
            "datesubmitted": "2013-07-16 01:18:05",
            "[question(8)]": "Learn more about Firefox",
            "[variable(\\"STANDARD_COMMENTS\\")]": "",
            "[variable(\\"STANDARD_GEODMA\\")]": "0",
            "status": "Complete",
            "[variable(\\"6-shown\\")]": "1",
            "[variable(\\"STANDARD_LAT\\")]": "23.266701",
            "[variable(\\"STANDARD_GEOPOSTAL\\")]": "",
            "[question(3), option(10004)]": "Help Articles\\n",
            "[variable(\\"STANDARD_IP\\")]": "111.111.11.11",
            "[variable(4)]": "10007",
            "is_test_data": "0",
            "[url(\\"_\\")]": "",
            "[variable(\\"STANDARD_GEOCITY\\")]": "Bhopal",
            "[url(\\"sguid\\")]": "",
            "[variable(2)]": "10001",
            "[variable(\\"STANDARD_GEOCOUNTRY\\")]": "India",
            "[variable(\\"3-shown\\")]": "1",
            "[question(3), option(10006)]": "",
            "[variable(\\"STANDARD_LONG\\")]": "77.400002",
            "[variable(8)]": "10018",
            "[question(3), option(10005)]": "Support Forum\\n"
        }, {
            "[variable(\\"8-shown\\")]": "1",
            "[variable(\\"1-shown\\")]": "1",
            "[variable(\\"4-shown\\")]": "1",
            "[variable(\\"2-shown\\")]": "1",
            "[variable(\\"7-shown\\")]": "1",
            "contact_id": "100020010",
            "[variable(\\"STANDARD_USERAGENT\\")]": "Mozilla/5.0 (Windows NT 5\
.1; rv:22.0) Gecko/20100101 Firefox/22.0",
            "[question(6)]": "i know  mozilla firefox has  very experienced te\
am what ever they are doing it is for the mankind and i can simply send best w\
ishes\\r\\nthanks  that u give honour to ordinary people like me",
            "[question(4)]": " 9\\r",
            "[variable(\\"STANDARD_GEOREGION\\")]": "35",
            "id": "3971",
            "[question(2)]": "I don't know\\n",
            "[variable(\\"PORTAL_RELATIONSHIP\\")]": "",
            "[variable(\\"STANDARD_REFERER\\")]": "http://in-mg61.mail.yahoo.c\
om/neo/launch",
            "[variable(\\"STANDARD_RESPONSETIME\\")]": "",
            "sResponseComment": "",
            "datesubmitted": "2013-07-16 01:18:05",
            "[question(8)]": "Learn more about Firefox",
            "[variable(\\"STANDARD_COMMENTS\\")]": "",
            "[variable(\\"STANDARD_GEODMA\\")]": "0",
            "status": "Complete",
            "[variable(\\"6-shown\\")]": "1",
            "[variable(\\"STANDARD_LAT\\")]": "23.266701",
            "[variable(\\"STANDARD_GEOPOSTAL\\")]": "",
            "[question(3), option(10004)]": "Help Articles\\n",
            "[variable(\\"STANDARD_IP\\")]": "111.111.11.11",
            "[variable(4)]": "10007",
            "is_test_data": "0",
            "[url(\\"_\\")]": "",
            "[variable(\\"STANDARD_GEOCITY\\")]": "Bhopal",
            "[url(\\"sguid\\")]": "",
            "[variable(2)]": "10001",
            "[variable(\\"STANDARD_GEOCOUNTRY\\")]": "India",
            "[variable(\\"3-shown\\")]": "1",
            "[question(3), option(10006)]": "",
            "[variable(\\"STANDARD_LONG\\")]": "77.400002",
            "[variable(8)]": "10018",
            "[question(3), option(10005)]": "Support Forum\\n"
        }, {
            "[variable(\\"8-shown\\")]": "1",
            "[variable(\\"1-shown\\")]": "1",
            "[variable(\\"4-shown\\")]": "1",
            "[variable(\\"2-shown\\")]": "1",
            "[variable(\\"7-shown\\")]": "1",
            "contact_id": "100020010",
            "[variable(\\"STANDARD_USERAGENT\\")]": "Mozilla/5.0 (Windows NT 5\
.1; rv:22.0) Gecko/20100101 Firefox/22.0",
            "[question(6)]": "i know  mozilla firefox has  very experienced te\
am what ever they are doing it is for the mankind and i can simply send best w\
ishes\\r\\nthanks  that u give honour to ordinary people like me",
            "[question(4)]": " 9\\r",
            "[variable(\\"STANDARD_GEOREGION\\")]": "35",
            "id": "3971",
            "[question(2)]": "Yes\\n",
            "[variable(\\"PORTAL_RELATIONSHIP\\")]": "",
            "[variable(\\"STANDARD_REFERER\\")]": "http://in-mg61.mail.yahoo.c\
om/neo/launch",
            "[variable(\\"STANDARD_RESPONSETIME\\")]": "",
            "sResponseComment": "",
            "datesubmitted": "2013-07-16 01:18:05",
            "[question(8)]": "Learn more about Firefox",
            "[variable(\\"STANDARD_COMMENTS\\")]": "",
            "[variable(\\"STANDARD_GEODMA\\")]": "0",
            "status": "Complete",
            "[variable(\\"6-shown\\")]": "1",
            "[variable(\\"STANDARD_LAT\\")]": "23.266701",
            "[variable(\\"STANDARD_GEOPOSTAL\\")]": "",
            "[question(3), option(10004)]": "Help Articles\\n",
            "[variable(\\"STANDARD_IP\\")]": "111.111.11.11",
            "[variable(4)]": "10007",
            "is_test_data": "0",
            "[url(\\"_\\")]": "",
            "[variable(\\"STANDARD_GEOCITY\\")]": "Bhopal",
            "[url(\\"sguid\\")]": "",
            "[variable(2)]": "10001",
            "[variable(\\"STANDARD_GEOCOUNTRY\\")]": "India",
            "[variable(\\"3-shown\\")]": "1",
            "[question(3), option(10006)]": "",
            "[variable(\\"STANDARD_LONG\\")]": "77.400002",
            "[variable(8)]": "10018",
            "[question(3), option(10005)]": "Support Forum\\n"
        }
    ],
    "page": "1"
}
"""
