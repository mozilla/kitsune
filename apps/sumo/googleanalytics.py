from datetime import timedelta

from django.conf import settings

import httplib2
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials


key = settings.GA_KEY
account = settings.GA_ACCOUNT
profile_id = settings.GA_PROFILE_ID


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
