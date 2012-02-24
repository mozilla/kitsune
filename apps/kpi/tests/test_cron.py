from datetime import date

from mock import patch
from nose.tools import eq_

from kpi.cron import update_visitors_metric, Webtrends
from kpi.models import Metric, VISITORS_METRIC_CODE
from kpi.tests import metric_kind
from sumo.tests import TestCase


class UpdateVisitorsTests(TestCase):
    @patch.object(Webtrends, 'visits')
    def test_update_visitors_cron(self, visits):
        """Verify the cron job inserts the right rows."""
        visitor_kind = metric_kind(code=VISITORS_METRIC_CODE, save=True)
        visits.return_value = {'2012-01-13': 42,
                               '2012-01-14': 193,
                               '2012-01-15': 33}

        update_visitors_metric()

        metrics = Metric.objects.filter(kind=visitor_kind)
        eq_(3, len(metrics))
        eq_(42, metrics[0].value)
        eq_(193, metrics[1].value)
        eq_(date(2012, 01, 15), metrics[2].start)
