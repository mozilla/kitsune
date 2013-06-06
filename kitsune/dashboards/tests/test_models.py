# -*- coding: utf-8 -*-
from mock import patch
from nose.tools import eq_

from kitsune.dashboards.models import (
    WikiDocumentVisits, LAST_7_DAYS, googleanalytics)
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import document, revision


class DocumentVisitsTests(TestCase):
    """Tests for the pageview statistics gathering."""

    @patch.object(googleanalytics, '_build_request')
    def test_visit_count_from_analytics(self, _build_request):
        """Verify stored visit counts from mocked analytics data.

        It has some nasty non-ASCII chars in it.
        """
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = PAGEVIEWS_BY_DOCUMENT_RESPONSE

        d1 = revision(document=document(slug='hellỗ', save=True),
                      is_approved=True, save=True).document
        d2 = revision(document=document(slug='there', save=True),
                      is_approved=True, save=True).document

        WikiDocumentVisits.reload_period_from_analytics(LAST_7_DAYS)

        eq_(2, WikiDocumentVisits.objects.count())
        wdv1 = WikiDocumentVisits.objects.get(document=d1)
        eq_(27, wdv1.visits)
        eq_(LAST_7_DAYS, wdv1.period)
        wdv2 = WikiDocumentVisits.objects.get(document=d2)
        eq_(LAST_7_DAYS, wdv2.period)


PAGEVIEWS_BY_DOCUMENT_RESPONSE = {
    u'kind': u'analytics#gaData',
    u'rows': [
        [u'/en-US/kb/hellỗ', u'27'],
        [u'/en-US/kb/hellỗ/edit', u'2'],
        [u'/en-US/kb/hellỗ/history', u'1'],
        [u'/en-US/kb/there', u'23'],
        [u'/en-US/kb/doc-3', u'10'],
        [u'/en-US/kb/doc-4', u'39'],
        [u'/en-US/kb/doc-5', u'40'],
        [u'/en-US/kb/doc-5/discuss', u'1'],
        [u'/en-US/kb/doc-5?param=ab', u'2'],
        [u'/en-US/kb/doc-5?param=cd', u'4']],
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
