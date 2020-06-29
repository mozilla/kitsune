from datetime import date

from unittest.mock import patch
from nose.tools import eq_

from kitsune.sumo import googleanalytics
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory


class GoogleAnalyticsTests(TestCase):
    """Tests for the Google Analytics API helper."""

    @patch.object(googleanalytics, '_build_request')
    def test_visitors(self, _build_request):
        """Test googleanalytics.visitors()."""
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = VISITORS_RESPONSE

        visits = googleanalytics.visitors(
            date(2013, 1, 16), date(2013, 1, 16))

        eq_(1, len(visits))
        eq_(382719, visits['2013-01-16'])

    @patch.object(googleanalytics, '_build_request')
    def test_visitors_by_locale(self, _build_request):
        """Test googleanalytics.visits_by_locale()."""
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = VISITORS_BY_LOCALE_RESPONSE

        visits = googleanalytics.visitors_by_locale(
            date(2013, 1, 16), date(2013, 1, 16))

        eq_(58, len(visits))
        eq_(221447, visits['en-US'])
        eq_(24432, visits['es'])

    @patch.object(googleanalytics, '_build_request')
    def test_pageviews_by_document(self, _build_request):
        """Test googleanalytics.pageviews_by_document()."""
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = PAGEVIEWS_BY_DOCUMENT_RESPONSE

        # Add some documents that match the response data.
        documents = []
        for i in range(1, 6):
            documents.append(ApprovedRevisionFactory(document__slug='doc-%s' % i).document)

        pageviews = googleanalytics.pageviews_by_document(
            date(2013, 1, 16), date(2013, 1, 16))

        eq_(5, len(pageviews))
        eq_(1, pageviews[documents[0].pk])
        eq_(2, pageviews[documents[1].pk])
        eq_(10, pageviews[documents[2].pk])
        eq_(39, pageviews[documents[3].pk])
        eq_(46, pageviews[documents[4].pk])

    @patch.object(googleanalytics, '_build_request')
    def test_pageviews_by_question(self, _build_request):
        """Test googleanalytics.pageviews_by_question()."""
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = PAGEVIEWS_BY_QUESTION_RESPONSE

        pageviews = googleanalytics.pageviews_by_question(
            date(2013, 1, 16), date(2013, 1, 16))

        eq_(3, len(pageviews))
        eq_(3, pageviews[1])
        eq_(2, pageviews[2])
        eq_(11, pageviews[3])

    @patch.object(googleanalytics, '_build_request')
    def test_search_ctr(self, _build_request):
        """Test googleanalytics.search_ctr()."""
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = SEARCH_CTR_RESPONSE

        ctr = googleanalytics.search_ctr(
            date(2013, 6, 6), date(2013, 6, 6))

        eq_(1, len(ctr))
        eq_(74.88925980111263, ctr['2013-06-06'])


VISITORS_RESPONSE = {
    'kind': 'analytics#gaData',
    'rows': [['382719']],  # <~ The number we are looking for.
    'containsSampledData': False,
    'profileInfo': {
        'webPropertyId': 'UA-1234567890',
        'internalWebPropertyId': '1234567890',
        'tableId': 'ga:1234567890',
        'profileId': '1234567890',
        'profileName': 'support.mozilla.org - Production Only',
        'accountId': '1234567890'},
    'itemsPerPage': 1000,
    'totalsForAllResults': {
        'ga:visitors': '382719'},
    'columnHeaders': [
        {'dataType': 'INTEGER',
         'columnType': 'METRIC',
         'name': 'ga:visitors'}],
    'query': {
        'max-results': 1000,
        'dimensions': '',
        'start-date': '2013-01-16',
        'start-index': 1,
        'ids': 'ga:1234567890',
        'metrics': ['ga:visitors'],
        'end-date': '2013-01-16'
    },
    'totalResults': 1,
    'id': ('https://www.googleapis.com/analytics/v3/data/ga'
           '?ids=ga:1234567890&metrics=ga:visitors&start-date=2013-01-16'
           '&end-date=2013-01-16'),
    'selfLink': ('https://www.googleapis.com/analytics/v3/data/ga'
                 '?ids=ga:1234567890&metrics=ga:visitors'
                 '&start-date=2013-01-16&end-date=2013-01-16')
}


VISITORS_BY_LOCALE_RESPONSE = {
    'kind': 'analytics#gaData',
    'rows': [
        ['/1/', '16'],
        ['/ach/', '24'],
        ['/ak/', '32'],
        ['/ar/', '3362'],
        ['/as/', '10'],
        ['/ast/', '6'],
        ['/az/', '41'],
        ['/be/', '13'],
        ['/bg/', '989'],
        ['/bn/', '21'],
        ['/bs/', '73'],
        ['/ca/', '432'],
        ['/cs/', '3308'],
        ['/da/', '947'],
        ['/de/', '37313'],
        ['/el/', '1720'],
        ['/en-US/', '221447'],
        ['/eo/', '12'],
        ['/es/', '24432'],
        ['/et/', '226'],
        ['/eu/', '122'],
        ['/fa/', '356'],
        ['/favicon.ico', '4'],
        ['/ff/', '6'],
        ['/fi/', '2318'],
        ['/fr/', '24922'],
        ['/fur/', '5'],
        ['/fy-NL/', '2'],
        ['/ga-IE/', '7'],
        ['/gd/', '7'],
        ['/gl/', '43'],
        ['/gu-IN/', '3'],
        ['/he/', '202'],
        ['/hi-IN/', '21'],
        ['/hr/', '677'],
        ['/hu/', '2873'],
        ['/hy-AM/', '14'],
        ['/id/', '3390'],
        ['/ilo/', '5'],
        ['/is/', '39'],
        ['/it/', '9986'],
        ['/ja/', '15508'],
        ['/kk/', '9'],
        ['/km/', '8'],
        ['/kn/', '7'],
        ['/ko/', '858'],
        ['/lt/', '536'],
        ['/mai/', '12'],
        ['/mk/', '58'],
        ['/ml/', '10'],
        ['/mn/', '42'],
        ['/mr/', '10'],
        ['/ms/', '14'],
        ['/my/', '413'],
        ['/nb-NO/', '714'],
        ['/ne-NP/', '7'],
        ['/nl/', '4970'],
        ['/no/', '135'],
        ['/pa-IN/', '10'],
        ['/pl/', '9701'],
        ['/pt-BR/', '12299'],
        ['/pt-PT/', '1332'],
        ['/rm/', '8'],
        ['/ro/', '1221'],
        ['/ru/', '26194'],
        ['/rw/', '5'],
        ['/si/', '21'],
        ['/sk/', '875'],
        ['/sl/', '530'],
        ['/son/', '1'],
        ['/sq/', '27'],
        ['/sr/', '256'],
        ['/sv/', '1488'],
        ['/ta-LK/', '13'],
        ['/ta/', '13'],
        ['/te/', '6'],
        ['/th/', '2936'],
        ['/tr/', '3470'],
        ['/uk/', '434'],
        ['/vi/', '4880'],
        ['/zh-CN/', '5640'],
        ['/zh-TW/', '3508']
    ],
    'containsSampledData': False,
    'profileInfo': {
        'webPropertyId': 'UA-1234567890',
        'internalWebPropertyId': '1234567890',
        'tableId': 'ga:1234567890',
        'profileId': '1234567890',
        'profileName': 'support.mozilla.org - Production Only',
        'accountId': '1234567890'
    },
    'itemsPerPage': 1000,
    'totalsForAllResults': {
        'ga:visitors': '437598'},
    'columnHeaders': [
        {'dataType': 'STRING',
         'columnType': 'DIMENSION',
         'name': 'ga:pagePathLevel1'},
        {'dataType': 'INTEGER',
         'columnType': 'METRIC',
         'name': 'ga:visitors'}
    ],
    'query': {
        'max-results': 1000,
        'dimensions': 'ga:pagePathLevel1',
        'start-date': '2013-01-16',
        'start-index': 1,
        'ids': 'ga:1234567890',
        'metrics': ['ga:visitors'],
        'end-date': '2013-01-16'
    },
    'totalResults': 83,
    'id': ('https://www.googleapis.com/analytics/v3/data/ga'
           '?ids=ga:1234567890&dimensions=ga:pagePathLevel1'
           '&metrics=ga:visitors&start-date=2013-01-16&end-date=2013-01-16'),
    'selfLink': ('https://www.googleapis.com/analytics/v3/data/ga'
                 '?ids=ga:1234567890&dimensions=ga:pagePathLevel1'
                 '&metrics=ga:visitors&start-date=2013-01-16'
                 '&end-date=2013-01-16'),
}


PAGEVIEWS_BY_DOCUMENT_RESPONSE = {
    'kind': 'analytics#gaData',
    'rows': [
        ['/en-US/kb/doc-1', '1'],  # Counts as a pageview.
        ['/en-US/kb/doc-1/edit', '2'],  # Doesn't count as a pageview
        ['/en-US/kb/doc-1/history', '1'],  # Doesn't count as a pageview
        ['/en-US/kb/doc-2', '2'],  # Counts as a pageview.
        ['/en-US/kb/doc-3', '10'],  # Counts as a pageview.
        ['/en-US/kb/doc-4', '39'],  # Counts as a pageview.
        ['/en-US/kb/doc-5', '40'],  # Counts as a pageview.
        ['/en-US/kb/doc-5/discuss', '1'],  # Doesn't count as a pageview
        ['/en-US/kb/doc-5?param=ab', '2'],  # Counts as a pageview.
        ['/en-US/kb/doc-5?param=cd', '4']],  # Counts as a pageview.
    'containsSampledData': False,
    'columnHeaders': [
        {'dataType': 'STRING',
         'columnType': 'DIMENSION',
         'name': 'ga:pagePath'},
        {'dataType': 'INTEGER',
         'columnType': 'METRIC',
         'name': 'ga:pageviews'}
    ],
    'profileInfo': {
        'webPropertyId': 'UA-1234567890',
        'internalWebPropertyId': '1234567890',
        'tableId': 'ga:1234567890',
        'profileId': '1234567890',
        'profileName': 'support.mozilla.org - Production Only',
        'accountId': '1234567890'},
    'itemsPerPage': 10,
    'totalsForAllResults': {
        'ga:pageviews': '164293'},
    'nextLink': ('https://www.googleapis.com/analytics/v3/data/ga'
                 '?ids=ga:1234567890&dimensions=ga:pagePath'
                 '&metrics=ga:pageviews&filters=ga:pagePathLevel2%3D%3D/kb/'
                 ';ga:pagePathLevel1%3D%3D/en-US/&start-date=2013-01-17'
                 '&end-date=2013-01-17&start-index=11&max-results=10'),
    'query': {
        'max-results': 10,
        'dimensions': 'ga:pagePath',
        'start-date': '2013-01-17',
        'start-index': 1,
        'ids': 'ga:1234567890',
        'metrics': ['ga:pageviews'],
        'filters': 'ga:pagePathLevel2==/kb/;ga:pagePathLevel1==/en-US/',
        'end-date': '2013-01-17'},
    'totalResults': 10,
    'id': ('https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890'
           '&dimensions=ga:pagePath&metrics=ga:pageviews'
           '&filters=ga:pagePathLevel2%3D%3D/kb/;'
           'ga:pagePathLevel1%3D%3D/en-US/&start-date=2013-01-17'
           '&end-date=2013-01-17&start-index=1&max-results=10'),
    'selfLink': ('https://www.googleapis.com/analytics/v3/data/ga'
                 '?ids=ga:1234567890&dimensions=ga:pagePath&'
                 'metrics=ga:pageviews&filters=ga:pagePathLevel2%3D%3D/kb/;'
                 'ga:pagePathLevel1%3D%3D/en-US/&start-date=2013-01-17'
                 '&end-date=2013-01-17&start-index=1&max-results=10')
}


PAGEVIEWS_BY_QUESTION_RESPONSE = {
    'columnHeaders': [
        {'columnType': 'DIMENSION',
         'dataType': 'STRING',
         'name': 'ga:pagePath'},
        {'columnType': 'METRIC',
         'dataType': 'INTEGER',
         'name': 'ga:pageviews'}],
    'containsSampledData': False,
    'id': ('https://www.googleapis.com/analytics/v3/data/ga?ids=ga:65912487'
           '&dimensions=ga:pagePath&metrics=ga:pageviews'
           '&filters=ga:pagePathLevel2%3D%3D/questions/&start-date=2013-01-01'
           '&end-date=2013-01-02&start-index=1&max-results=10'),
    'itemsPerPage': 10,
    'kind': 'analytics#gaData',
    'nextLink': ('https://www.googleapis.com/analytics/v3/data/ga'
                 '?ids=ga:65912487&dimensions=ga:pagePath'
                 '&metrics=ga:pageviews'
                 '&filters=ga:pagePathLevel2%3D%3D/questions/'
                 '&start-date=2013-01-01&end-date=2013-01-02'
                 '&start-index=11&max-results=10'),
    'profileInfo': {
        'accountId': '36116321',
        'internalWebPropertyId': '64136921',
        'profileId': '65912487',
        'profileName': 'support.mozilla.org - Production Only',
        'tableId': 'ga:65912487',
        'webPropertyId': 'UA-36116321-2'},
    'query': {
        'dimensions': 'ga:pagePath',
        'end-date': '2013-01-02',
        'filters': 'ga:pagePathLevel2==/questions/',
        'ids': 'ga:65912487',
        'max-results': 10,
        'metrics': ['ga:pageviews'],
        'start-date': '2013-01-01',
        'start-index': 1},
    'rows': [
        ['/en-US/questions/1', '2'],  # Counts as a pageview.
        ['/es/questions/1', '1'],  # Counts as a pageview.
        ['/en-US/questions/1/edit', '3'],  # Doesn't count as a pageview
        ['/en-US/questions/stats', '1'],  # Doesn't count as a pageview
        ['/en-US/questions/2', '1'],  # Counts as a pageview.
        ['/en-US/questions/2?mobile=1', '1'],  # Counts as a pageview.
        ['/en-US/questions/2/foo', '2'],  # Doesn't count as a pageview
        ['/en-US/questions/bar', '1'],  # Doesn't count as a pageview
        ['/es/questions/3?mobile=0', '10'],  # Counts as a pageview.
        ['/es/questions/3?lang=en-US', '1']],  # Counts as a pageview.
    'selfLink': ('https://www.googleapis.com/analytics/v3/data/ga'
                 '?ids=ga:65912487&dimensions=ga:pagePath'
                 '&metrics=ga:pageviews'
                 '&filters=ga:pagePathLevel2%3D%3D/questions/'
                 '&start-date=2013-01-01&end-date=2013-01-02'
                 '&start-index=1&max-results=10'),
    'totalResults': 10,
    'totalsForAllResults': {'ga:pageviews': '242403'}}


SEARCH_CTR_RESPONSE = {
    'kind': 'analytics#gaData',
    'rows': [['74.88925980111263']],  # <~ The number we are looking for.
    'containsSampledData': False,
    'profileInfo': {
        'webPropertyId': 'UA-36116321-2',
        'internalWebPropertyId': '64136921',
        'tableId': 'ga:65912487',
        'profileId': '65912487',
        'profileName': 'support.mozilla.org - Production Only',
        'accountId': '36116321'},
    'itemsPerPage': 1000,
    'totalsForAllResults': {
        'ga:goal11ConversionRate': '74.88925980111263'},
    'columnHeaders': [
        {'dataType': 'PERCENT',
         'columnType': 'METRIC',
         'name': 'ga:goal11ConversionRate'}],
    'query': {
        'max-results': 1000,
        'start-date': '2013-06-06',
        'start-index': 1,
        'ids': 'ga:65912487',
        'metrics': ['ga:goal11ConversionRate'],
        'end-date': '2013-06-06'},
    'totalResults': 1,
    'id': ('https://www.googleapis.com/analytics/v3/data/ga?ids=ga:65912487'
           '&metrics=ga:goal11ConversionRate&start-date=2013-06-06'
           '&end-date=2013-06-06'),
    'selfLink': ('https://www.googleapis.com/analytics/v3/data/ga'
                 '?ids=ga:65912487&metrics=ga:goal11ConversionRate&'
                 'start-date=2013-06-06&end-date=2013-06-06'),
}
