from datetime import datetime, date
import json
from urllib2 import HTTPBasicAuthHandler, build_opener

from django.conf import settings

from sumo.helpers import urlparams


class StatsException(Exception):
    """An error in the stats returned by the third-party analytics package"""
    def __init__(self, msg):
        self.msg = msg


class StatsIOError(IOError):
    """An error communicating with WebTrends"""


class Webtrends(object):
    """Webtrends API helper."""

    @classmethod
    def request(cls, url, start, end, realm='Webtrends Basic Authentication'):
        """Make an authed request to the webtrends API.

        Make one attempt to fetch and reload the data. If something fails, it's
        the caller's responsibility to retry.
        """

        # If start and/or end are date or datetime, convert to string.
        if isinstance(start, (date, datetime)):
            start = start.strftime('%Ym%md%d')
        if isinstance(end, (date, datetime)):
            end = end.strftime('%Ym%md%d')

        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(realm=realm,
                                  uri=url,
                                  user=settings.WEBTRENDS_USER,
                                  passwd=settings.WEBTRENDS_PASSWORD)
        opener = build_opener(auth_handler)
        url = urlparams(url, start_period=start, end_period=end)
        try:
            # TODO: A wrong username or password results in a recursion depth
            # error.
            return opener.open(url).read()
        except IOError, e:
            raise StatsIOError(*e.args)

    @classmethod
    def wiki_report(cls, start, end):
        """Return the json for the wiki article visits report."""
        return cls.request(settings.WEBTRENDS_WIKI_REPORT_URL, start, end)

    @classmethod
    def key_metrics(cls, start, end):
        """Return the json result for the KeyMetrics API call."""
        url = ('https://ws.webtrends.com/v3/Reporting/profiles/{profile_id}'
               '/KeyMetrics/?period_type=trend')
        url = url.format(profile_id=settings.WEBTRENDS_PROFILE_ID)
        return cls.request(url, start, end, realm='DX')

    @classmethod
    def visits(cls, start, end):
        """Return the number of unique visitors.

        Returns a dict with daily numbers:
            {u'2012-01-22': 404971,
             u'2012-01-23': 434618,
             u'2012-01-24': 501687,...}
        """
        data = json.loads(cls.key_metrics(start, end))
        rows = data['data'][0][settings.WEBTRENDS_PROFILE_ID]['SubRows']
        if not isinstance(rows, list):
            rows = [rows]

        visits = {}
        for row in rows:
            visits[row['start_date']] = row['measures']['Visitors']

        return visits

    @classmethod
    def visits_by_locale(cls, start, end):
        """Return the number of unique visits by locale.

        Returns a dict with visits for each locale:
            {u'en-US': 7683415,
             u'de': 1293052,
             u'es': 830521,...}
        """
        url = ('https://ws.webtrends.com/v2_1/ReportService/profiles/'
               '{profile_id}/reports/FRnJo3T7MM6/?format=json')
        url = url.format(profile_id=settings.WEBTRENDS_PROFILE_ID)

        data = json.loads(cls.request(url, start, end))['data']
        locales = data[data.keys()[0]]['SubRows']

        visits = {}
        for url, info in locales.iteritems():
            locale = url.split('/')[-1]

            if locale not in settings.SUMO_LANGUAGES:
                # Filter out non locales like /admin.
                continue

            count = info['measures']['Visits']

            # Locales can appear twice due to .com to .org change.
            if locale in visits:
                visits[locale] += count
            else:
                visits[locale] = count

        return visits
