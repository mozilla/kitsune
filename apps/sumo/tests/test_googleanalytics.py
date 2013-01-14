from datetime import date

from mock import patch
from nose.tools import eq_

from sumo.tests import TestCase
from sumo import googleanalytics


VISITORS_RESPONSE = {u'kind': u'analytics#gaData', u'rows': [[u'382719']], u'containsSampledData': False, u'profileInfo': {u'webPropertyId': u'UA-1234567890', u'internalWebPropertyId': u'1234567890', u'tableId': u'ga:1234567890', u'profileId': u'1234567890', u'profileName': u'support.mozilla.org - Production Only', u'accountId': u'1234567890'}, u'itemsPerPage': 1000, u'totalsForAllResults': {u'ga:visitors': u'382719'}, u'columnHeaders': [{u'dataType': u'INTEGER', u'columnType': u'METRIC', u'name': u'ga:visitors'}], u'query': {u'max-results': 1000, u'dimensions': u'', u'start-date': u'2013-01-16', u'start-index': 1, u'ids': u'ga:1234567890', u'metrics': [u'ga:visitors'], u'end-date': u'2013-01-16'}, u'totalResults': 1, u'id': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&metrics=ga:visitors&start-date=2013-01-16&end-date=2013-01-16', u'selfLink': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&metrics=ga:visitors&start-date=2013-01-16&end-date=2013-01-16'}


class GoogleAnalyticsTests(TestCase):
    """Tests for the Google Analytics API helper."""

    @patch.object(googleanalytics, '_build_request')
    def test_visitors(self, _build_request):
        """Test googleanalytics.visitors()."""
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = VISITORS_RESPONSE

        visits = googleanalytics.visitors(
            date(2013, 01, 16), date(2013, 01, 16))

        eq_(1, len(visits))
        eq_(382719, visits['2013-01-16'])
