from datetime import date, timedelta

from mock import patch
from nose.tools import eq_

import kitsune.kpi.cron
from kitsune.kpi import surveygizmo_utils
from kitsune.kpi.cron import (
    update_visitors_metric, update_l10n_metric, googleanalytics,
    update_search_ctr_metric, _process_exit_survey_results)
from kitsune.kpi.models import (
    Metric, VISITORS_METRIC_CODE, L10N_METRIC_CODE, SEARCH_CLICKS_METRIC_CODE,
    SEARCH_SEARCHES_METRIC_CODE, EXIT_SURVEY_YES_CODE, EXIT_SURVEY_NO_CODE,
    EXIT_SURVEY_DONT_KNOW_CODE)
from kitsune.kpi.tests import metric_kind, metric
from kitsune.sumo.tests import TestCase
from kitsune.wiki.config import (
    MAJOR_SIGNIFICANCE, MEDIUM_SIGNIFICANCE, TYPO_SIGNIFICANCE)
from kitsune.wiki.tests import document, revision


class CronJobTests(TestCase):
    @patch.object(googleanalytics, 'visitors')
    def test_update_visitors_cron(self, visitors):
        """Verify the cron job inserts the right rows."""
        visitor_kind = metric_kind(code=VISITORS_METRIC_CODE, save=True)
        visitors.return_value = {'2012-01-13': 42,
                                 '2012-01-14': 193,
                                 '2012-01-15': 33}

        update_visitors_metric()

        metrics = Metric.objects.filter(kind=visitor_kind).order_by('start')
        eq_(3, len(metrics))
        eq_(42, metrics[0].value)
        eq_(193, metrics[1].value)
        eq_(date(2012, 01, 15), metrics[2].start)

    @patch.object(kitsune.kpi.cron, '_get_top_docs')
    @patch.object(googleanalytics, 'visitors_by_locale')
    def test_update_l10n_metric_cron(self, visitors_by_locale, _get_top_docs):
        """Verify the cron job creates the correct metric."""
        l10n_kind = metric_kind(code=L10N_METRIC_CODE, save=True)

        # Create the en-US document with an approved revision.
        doc = document(save=True)
        rev = revision(
            document=doc,
            significance=MEDIUM_SIGNIFICANCE,
            is_approved=True,
            is_ready_for_localization=True,
            save=True)

        # Create an es translation that is up to date.
        es_doc = document(parent=doc, locale='es', save=True)
        revision(
            document=es_doc,
            is_approved=True,
            based_on=rev,
            save=True)

        # Create a de translation without revisions.
        document(parent=doc, locale='de', save=True)

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
        revision(
            document=doc,
            significance=TYPO_SIGNIFICANCE,
            is_approved=True,
            is_ready_for_localization=True,
            save=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(75, metrics[0].value)

        # Create a new revision with MEDIUM_SIGNIFICANCE. The coverage
        # should now be 62% (0.5/1 * 25/100 + 1/1 * 50/100)
        m1 = revision(
            document=doc,
            significance=MEDIUM_SIGNIFICANCE,
            is_approved=True,
            is_ready_for_localization=True,
            save=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(62, metrics[0].value)

        # And another new revision with MEDIUM_SIGNIFICANCE makes the
        # coverage 50% (1/1 * 50/100).
        m2 = revision(
            document=doc,
            significance=MEDIUM_SIGNIFICANCE,
            is_approved=True,
            is_ready_for_localization=True,
            save=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(50, metrics[0].value)

        # If we remove the two MEDIUM_SIGNIFICANCE revisions and add a
        # MAJOR_SIGNIFICANCE revision, the coverage is 50% as well.
        m1.delete()
        m2.delete()
        revision(
            document=doc,
            significance=MAJOR_SIGNIFICANCE,
            is_approved=True,
            is_ready_for_localization=True,
            save=True)
        Metric.objects.all().delete()
        update_l10n_metric()
        metrics = Metric.objects.filter(kind=l10n_kind)
        eq_(1, len(metrics))
        eq_(50, metrics[0].value)

    @patch.object(googleanalytics, 'search_ctr')
    def test_update_search_ctr(self, search_ctr):
        """Verify the cron job inserts the right rows."""
        clicks_kind = metric_kind(code=SEARCH_CLICKS_METRIC_CODE, save=True)
        metric_kind(code=SEARCH_SEARCHES_METRIC_CODE, save=True)
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
        yes_kind = metric_kind(code=EXIT_SURVEY_YES_CODE, save=True)
        no_kind = metric_kind(code=EXIT_SURVEY_NO_CODE, save=True)
        dunno_kind = metric_kind(code=EXIT_SURVEY_DONT_KNOW_CODE, save=True)
        two_days_back = date.today() - timedelta(days=2)

        # Add a metric for 2 days ago so only 1 new day is collected.
        metric(kind=yes_kind, start=two_days_back, save=True)

        # Collect and process.
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
