from datetime import date

from mock import patch
from nose.tools import eq_

from sumo.tests import TestCase
from sumo import googleanalytics
from wiki.tests import document, revision


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

    @patch.object(googleanalytics, '_build_request')
    def test_visitors_by_locale(self, _build_request):
        """Test googleanalytics.visits_by_locale()."""
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = VISITORS_BY_LOCALE_RESPONSE

        visits = googleanalytics.visitors_by_locale(
            date(2013, 01, 16), date(2013, 01, 16))

        eq_(81, len(visits))
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
            documents.append(revision(
                document=document(slug='doc-%s' % i, save=True),
                is_approved=True,
                save=True).document)

        pageviews = googleanalytics.pageviews_by_document(
            date(2013, 01, 16), date(2013, 01, 16))

        eq_(5, len(pageviews))
        eq_(1, pageviews[documents[0].pk])
        eq_(2, pageviews[documents[1].pk])
        eq_(10, pageviews[documents[2].pk])
        eq_(39, pageviews[documents[3].pk])
        eq_(46, pageviews[documents[4].pk])


VISITORS_RESPONSE = {
    u'kind': u'analytics#gaData',
    u'rows': [[u'382719']],  # <~ The number we are looking for.
    u'containsSampledData': False,
    u'profileInfo': {
        u'webPropertyId': u'UA-1234567890',
        u'internalWebPropertyId': u'1234567890',
        u'tableId': u'ga:1234567890',
        u'profileId': u'1234567890',
        u'profileName': u'support.mozilla.org - Production Only',
        u'accountId': u'1234567890'},
    u'itemsPerPage': 1000,
    u'totalsForAllResults': {
        u'ga:visitors': u'382719'},
    u'columnHeaders': [
        {u'dataType': u'INTEGER',
         u'columnType': u'METRIC',
         u'name': u'ga:visitors'}],
    u'query': {
        u'max-results': 1000,
        u'dimensions': u'',
        u'start-date': u'2013-01-16',
        u'start-index': 1,
        u'ids': u'ga:1234567890',
        u'metrics': [u'ga:visitors'],
        u'end-date': u'2013-01-16'},
        u'totalResults': 1,
        u'id': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&metrics=ga:visitors&start-date=2013-01-16&end-date=2013-01-16',
        u'selfLink': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&metrics=ga:visitors&start-date=2013-01-16&end-date=2013-01-16'}


VISITORS_BY_LOCALE_RESPONSE = {
    u'kind': u'analytics#gaData',
    u'rows': [
        [u'/1/', u'16'],
        [u'/ach/', u'24'],
        [u'/ak/', u'32'],
        [u'/ar/', u'3362'],
        [u'/as/', u'10'],
        [u'/ast/', u'6'],
        [u'/be/', u'13'],
        [u'/bg/', u'989'],
        [u'/bn-BD/', u'21'],
        [u'/bn-IN/', u'3'],
        [u'/bs/', u'73'],
        [u'/ca/', u'432'],
        [u'/cs/', u'3308'],
        [u'/da/', u'947'],
        [u'/de/', u'37313'],
        [u'/el/', u'1720'],
        [u'/en-US/', u'221447'],
        [u'/eo/', u'12'],
        [u'/es/', u'24432'],
        [u'/et/', u'226'],
        [u'/eu/', u'122'],
        [u'/fa/', u'356'],
        [u'/favicon.ico', u'4'],
        [u'/ff/', u'6'],
        [u'/fi/', u'2318'],
        [u'/fr/', u'24922'],
        [u'/fur/', u'5'],
        [u'/fy-NL/', u'2'],
        [u'/ga-IE/', u'7'],
        [u'/gd/', u'7'],
        [u'/gl/', u'43'],
        [u'/gu-IN/', u'3'],
        [u'/he/', u'202'],
        [u'/hi-IN/', u'21'],
        [u'/hr/', u'677'],
        [u'/hu/', u'2873'],
        [u'/hy-AM/', u'14'],
        [u'/id/', u'3390'],
        [u'/ilo/', u'5'],
        [u'/is/', u'39'],
        [u'/it/', u'9986'],
        [u'/ja/', u'15508'],
        [u'/kk/', u'9'],
        [u'/km/', u'8'],
        [u'/kn/', u'7'],
        [u'/ko/', u'858'],
        [u'/lt/', u'536'],
        [u'/mai/', u'12'],
        [u'/mk/', u'58'],
        [u'/ml/', u'10'],
        [u'/mn/', u'42'],
        [u'/mr/', u'10'],
        [u'/ms/', u'14'],
        [u'/my/', u'413'],
        [u'/nb-NO/', u'714'],
        [u'/ne-NP/', u'7'],
        [u'/nl/', u'4970'],
        [u'/no/', u'135'],
        [u'/pa-IN/', u'10'],
        [u'/pl/', u'9701'],
        [u'/pt-BR/', u'12299'],
        [u'/pt-PT/', u'1332'],
        [u'/rm/', u'8'],
        [u'/ro/', u'1221'],
        [u'/ru/', u'26194'],
        [u'/rw/', u'5'],
        [u'/si/', u'21'],
        [u'/sk/', u'875'],
        [u'/sl/', u'530'],
        [u'/son/', u'1'],
        [u'/sq/', u'27'],
        [u'/sr-CYRL/', u'256'],
        [u'/sr-LATN/', u'31'],
        [u'/sv/', u'1488'],
        [u'/ta-LK/', u'13'],
        [u'/ta/', u'13'],
        [u'/te/', u'6'],
        [u'/th/', u'2936'],
        [u'/tr/', u'3470'],
        [u'/uk/', u'434'],
        [u'/vi/', u'4880'],
        [u'/zh-CN/', u'5640'],
        [u'/zh-TW/', u'3508']],
    u'containsSampledData': False,
    u'profileInfo': {
        u'webPropertyId': u'UA-1234567890',
        u'internalWebPropertyId': u'1234567890',
        u'tableId': u'ga:1234567890',
        u'profileId': u'1234567890',
        u'profileName': u'support.mozilla.org - Production Only',
        u'accountId': u'1234567890'},
    u'itemsPerPage': 1000,
    u'totalsForAllResults': {
        u'ga:visitors': u'437598'},
    u'columnHeaders': [
        {u'dataType': u'STRING',
         u'columnType': u'DIMENSION',
         u'name': u'ga:pagePathLevel1'},
        {u'dataType': u'INTEGER',
         u'columnType': u'METRIC',
         u'name': u'ga:visitors'}],
    u'query': {
        u'max-results': 1000,
        u'dimensions': u'ga:pagePathLevel1',
        u'start-date': u'2013-01-16',
        u'start-index': 1,
        u'ids': u'ga:1234567890',
        u'metrics': [u'ga:visitors'],
        u'end-date': u'2013-01-16'},
    u'totalResults': 83,
    u'id': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&dimensions=ga:pagePathLevel1&metrics=ga:visitors&start-date=2013-01-16&end-date=2013-01-16',
    u'selfLink': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&dimensions=ga:pagePathLevel1&metrics=ga:visitors&start-date=2013-01-16&end-date=2013-01-16'}


PAGEVIEWS_BY_DOCUMENT_RESPONSE = {
    u'kind': u'analytics#gaData',
    u'rows': [
        [u'/en-US/kb/doc-1', u'1'],  # Counts as a pageview.
        [u'/en-US/kb/doc-1/edit', u'2'],  # Doesn't count as a pageview (different view)
        [u'/en-US/kb/doc-1/history', u'1'],  # Doesn't count as a pageview (different view)
        [u'/en-US/kb/doc-2', u'2'],  # Counts as a pageview.
        [u'/en-US/kb/doc-3', u'10'],  # Counts as a pageview.
        [u'/en-US/kb/doc-4', u'39'],  # Counts as a pageview.
        [u'/en-US/kb/doc-5', u'40'],  # Counts as a pageview.
        [u'/en-US/kb/doc-5/discuss', u'1'],  # Doesn't count as a pageview (different view)
        [u'/en-US/kb/doc-5?param=ab', u'2'],  # Counts as a pageview.
        [u'/en-US/kb/doc-5?param=cd', u'4']],  # Counts as a pageview.
    u'containsSampledData': False,
    u'columnHeaders': [
        {u'dataType': u'STRING',
         u'columnType': u'DIMENSION',
         u'name': u'ga:pagePath'},
        {u'dataType': u'INTEGER',
         u'columnType': u'METRIC',
         u'name': u'ga:pageviews'}],
        u'profileInfo': {
            u'webPropertyId': u'UA-1234567890',
            u'internalWebPropertyId': u'1234567890',
            u'tableId': u'ga:1234567890',
            u'profileId': u'1234567890',
            u'profileName': u'support.mozilla.org - Production Only',
            u'accountId': u'1234567890'},
        u'itemsPerPage': 10,
        u'totalsForAllResults': {
            u'ga:pageviews': u'164293'},
        u'nextLink': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&dimensions=ga:pagePath&metrics=ga:pageviews&filters=ga:pagePathLevel2%3D%3D/kb/;ga:pagePathLevel1%3D%3D/en-US/&start-date=2013-01-17&end-date=2013-01-17&start-index=11&max-results=10',
        u'query': {
            u'max-results': 10,
            u'dimensions': u'ga:pagePath',
            u'start-date': u'2013-01-17',
            u'start-index': 1,
            u'ids': u'ga:1234567890',
            u'metrics': [u'ga:pageviews'],
            u'filters': u'ga:pagePathLevel2==/kb/;ga:pagePathLevel1==/en-US/',
            u'end-date': u'2013-01-17'},
        u'totalResults': 10,
        u'id': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&dimensions=ga:pagePath&metrics=ga:pageviews&filters=ga:pagePathLevel2%3D%3D/kb/;ga:pagePathLevel1%3D%3D/en-US/&start-date=2013-01-17&end-date=2013-01-17&start-index=1&max-results=10',
        u'selfLink': u'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:1234567890&dimensions=ga:pagePath&metrics=ga:pageviews&filters=ga:pagePathLevel2%3D%3D/kb/;ga:pagePathLevel1%3D%3D/en-US/&start-date=2013-01-17&end-date=2013-01-17&start-index=1&max-results=10'}
