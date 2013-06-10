import logging
from datetime import timedelta
from functools import wraps

from django.conf import settings

import httplib2
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials

from kitsune.questions.models import Question
from kitsune.wiki.models import Document


log = logging.getLogger('k.googleanalytics')


key = settings.GA_KEY
account = settings.GA_ACCOUNT
profile_id = settings.GA_PROFILE_ID


def retry_503(f):
    """Call `f`. If `f` raises an HTTP 503 exception, try again once.

    This is what Google Analytics recommends:
    https://developers.google.com/analytics/devguides/config/mgmt/v3/errors
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HttpError as e:
            log.error('HTTP Error calling Google Analytics: %s', e)

            if e.resp.status == 503:
                return f(*args, **kwargs)

    return wrapper


def _build_request():
    scope = 'https://www.googleapis.com/auth/analytics.readonly'
    creds = SignedJwtAssertionCredentials(account, key, scope)
    request = creds.authorize(httplib2.Http())
    service = build('analytics', 'v3', request)
    return service.data().ga()


def visitors(start_date, end_date):
    """Return the number of daily unique visitors for a given date range.

    Returns a dict with daily numbers:
        {u'2012-01-22': 404971,
         u'2012-01-23': 434618,
         u'2012-01-24': 501687,...}
    """
    visitors = {}
    request = _build_request()
    date = start_date
    while date <= end_date:
        date_str = str(date)
        visitors[str(date)] = int(request.get(
            ids='ga:' + profile_id,
            start_date=date_str,
            end_date=date_str,
            metrics='ga:visitors').execute()['rows'][0][0])
        date += timedelta(days=1)
    return visitors


def visitors_by_locale(start_date, end_date):
    """Return the number of unique visits by locale in a given date range.

    Returns a dict with visits for each locale:
        {u'en-US': 7683415,
         u'de': 1293052,
         u'es': 830521,...}
    """
    visits_by_locale = {}
    request = _build_request()

    @retry_503
    def _make_request():
        return request.get(
            ids='ga:' + profile_id,
            start_date=str(start_date),
            end_date=str(end_date),
            metrics='ga:visitors',
            dimensions='ga:pagePathLevel1').execute()

    results = _make_request()

    for result in results['rows']:
        path = result[0][1:-1]  # Strip leading and trailing slash.
        visitors = int(result[1])
        if path in settings.SUMO_LANGUAGES:
            visits_by_locale[path] = visitors

    return visits_by_locale


def pageviews_by_document(start_date, end_date):
    """Return the number of pageviews by document in a given date range.

    * Only returns en-US documents for now since that's what we did with
    webtrends.

    Returns a dict with pageviews for each document:
        {<document_id>: <pageviews>,
         1: 42,
         7: 1337,...}
    """
    counts = {}
    request = _build_request()
    start_index = 1
    max_results = 10000

    while True:  # To deal with pagination

        @retry_503
        def _make_request():
            return request.get(
                ids='ga:' + profile_id,
                start_date=str(start_date),
                end_date=str(end_date),
                metrics='ga:pageviews',
                dimensions='ga:pagePath',
                filters='ga:pagePathLevel2==/kb/;ga:pagePathLevel1==/en-US/',
                max_results=max_results,
                start_index=start_index).execute()

        results = _make_request()

        for result in results['rows']:
            path = result[0]
            pageviews = int(result[1])
            doc = Document.from_url(path, id_only=True, check_host=False)
            if not doc:
                continue

            # The same document can appear multiple times due to url params.
            counts[doc.pk] = counts.get(doc.pk, 0) + pageviews

        # Move to next page of results.
        start_index += max_results
        if start_index > results['totalResults']:
            break

    return counts


def pageviews_by_question(start_date, end_date):
    """Return the number of pageviews by question in a given date range.

    Returns a dict with pageviews for each document:
        {question_id>: <pageviews>,
         1: 42,
         7: 1337,...}
    """
    counts = {}
    request = _build_request()
    start_index = 1
    max_results = 10000

    while True:  # To deal with pagination

        @retry_503
        def _make_request():
            return request.get(
                ids='ga:' + profile_id,
                start_date=str(start_date),
                end_date=str(end_date),
                metrics='ga:pageviews',
                dimensions='ga:pagePath',
                filters='ga:pagePathLevel2==/questions/',
                max_results=max_results,
                start_index=start_index).execute()

        results = _make_request()

        for result in results['rows']:
            path = result[0]
            pageviews = int(result[1])
            question_id = Question.from_url(path, id_only=True)
            if not question_id:
                continue

            # The same question can appear multiple times due to url params
            # and locale.
            counts[question_id] = counts.get(question_id, 0) + pageviews

        # Move to next page of results.
        start_index += max_results
        if start_index > results['totalResults']:
            break

    return counts


def search_ctr(start_date, end_date):
    """Return search click through rate based on Goal 11 in google analytics.

    Returns a dict with daily numbers:
        {u'2012-01-22': 74.8,
         u'2012-01-23': 73.6,
         u'2012-01-24': 76.2,...}
    """
    ctr = {}
    request = _build_request()
    date = start_date
    while date <= end_date:
        date_str = str(date)

        # This metric name for goals in Google Analytics is gross.
        # Sorry about that. I don't see another way to it.
        metric_name = 'ga:goal11ConversionRate'
        ctr_str = request.get(
            ids='ga:' + profile_id,
            start_date=date_str,
            end_date=date_str,
            metrics=metric_name).execute()['rows'][0][0]
        ctr[date_str] = float(ctr_str)

        date += timedelta(days=1)

    return ctr
