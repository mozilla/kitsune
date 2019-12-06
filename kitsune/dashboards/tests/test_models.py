# -*- coding: utf-8 -*-
from mock import patch
from nose.tools import eq_

from kitsune.dashboards import models
from kitsune.dashboards.models import (
    WikiDocumentVisits, LAST_7_DAYS, googleanalytics)
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import ApprovedRevisionFactory


class DocumentVisitsTests(TestCase):
    """Tests for the pageview statistics gathering."""

    # Need to monkeypatch close_old_connections out because it
    # does something screwy with the testing infra around transactions.
    @patch.object(models, 'close_old_connections')
    @patch.object(googleanalytics, '_build_request')
    def test_visit_count_from_analytics(self, _build_request,
                                        close_old_connections):
        """Verify stored visit counts from mocked analytics data.

        It has some nasty non-ASCII chars in it.
        """
        execute = _build_request.return_value.get.return_value.execute
        execute.return_value = PAGEVIEWS_BY_DOCUMENT_RESPONSE

        d1 = ApprovedRevisionFactory(document__slug='hellỗ').document
        d2 = ApprovedRevisionFactory(document__slug='there').document

        WikiDocumentVisits.reload_period_from_analytics(LAST_7_DAYS)

        eq_(2, WikiDocumentVisits.objects.count())
        wdv1 = WikiDocumentVisits.objects.get(document=d1)
        eq_(27, wdv1.visits)
        eq_(LAST_7_DAYS, wdv1.period)
        wdv2 = WikiDocumentVisits.objects.get(document=d2)
        eq_(LAST_7_DAYS, wdv2.period)


PAGEVIEWS_BY_DOCUMENT_RESPONSE = {
    'kind': 'analytics#gaData',
    'rows': [
        ['/en-US/kb/hellỗ', '27'],
        ['/en-US/kb/hellỗ/edit', '2'],
        ['/en-US/kb/hellỗ/history', '1'],
        ['/en-US/kb/there', '23'],
        ['/en-US/kb/doc-3', '10'],
        ['/en-US/kb/doc-4', '39'],
        ['/en-US/kb/doc-5', '40'],
        ['/en-US/kb/doc-5/discuss', '1'],
        ['/en-US/kb/doc-5?param=ab', '2'],
        ['/en-US/kb/doc-5?param=cd', '4']],
    'containsSampledData': False,
    'columnHeaders': [
        {'dataType': 'STRING',
         'columnType': 'DIMENSION',
         'name': 'ga:pagePath'},
        {'dataType': 'INTEGER',
         'columnType': 'METRIC',
         'name': 'ga:pageviews'}],
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
    'nextLink': (
        'https://www.googleapis.com/analytics/v3/data/ga'
        '?ids=ga:1234567890&dimensions=ga:pagePath&metrics=ga:pageviews'
        '&filters=ga:pagePathLevel2%3D%3D/kb/;ga:pagePathLevel1%3D%3D/en-US/'
        '&start-date=2013-01-17&end-date=2013-01-17&start-index=11'
        '&max-results=10'),
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
    'id': (
        'https://www.googleapis.com/analytics/v3/data/ga'
        '?ids=ga:1234567890&dimensions=ga:pagePath&metrics=ga:pageviews'
        '&filters=ga:pagePathLevel2%3D%3D/kb/;ga:pagePathLevel1%3D%3D/en-US/'
        '&start-date=2013-01-17&end-date=2013-01-17&start-index=1'
        '&max-results=10'),
    'selfLink': (
        'https://www.googleapis.com/analytics/v3/data/ga'
        '?ids=ga:1234567890&dimensions=ga:pagePath&metrics=ga:pageviews'
        '&filters=ga:pagePathLevel2%3D%3D/kb/;ga:pagePathLevel1%3D%3D/en-US/'
        '&start-date=2013-01-17&end-date=2013-01-17&start-index=1'
        '&max-results=10')}
