#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Grab a bunch of emails from our email collector survey and add them to the
email campaign of the exit survey.

The exit survey email campaign will email the users and take care of the rest.

This script should be called from a daily cron job as follows:

    python add_new_emails_to_exit_survey.py -u USERNAME -p PASSWORD

USERNAME and PASSWORD are the SurveyGizmo credentials.

"""

import json
import optparse
import sys
from datetime import datetime, timedelta, date

try:
    import requests
except ImportError:
    print 'You need to install requests.  Do:'
    print ''
    print '   pip install requests'
    sys.exit()


USAGE = ('usage: %prog --username USERNAME --password PASSWORD --start START'
         ' --end END')
EMAIL_COLLECTION_SURVEY_ID = 1002970
EXIT_SURVEY_ID = 991425
EXIT_SURVEY_CAMPAIGN_ID = 878533


def get_email_addresses(startdate, enddate, user, password):
    """Get the email addresses collected between startdate and enddate."""
    emails = []
    page = 1
    more_pages = True

    while more_pages:
        response = requests.get(
            'https://restapi.surveygizmo.com/v2/survey/{survey}'
            '/surveyresponse?'
            'filter[field][0]=datesubmitted'
            '&filter[operator][0]=>=&filter[value][0]={start}+0:0:0'
            '&filter[operator][1]=<&filter[value][1]={end}+0:0:0'
            '&filter[field][1]=status&filter[operator][1]=='
            '&filter[value][1]=Complete'
            '&resultsperpage=500'
            '&page={page}'
            '&user:pass={user}:{password}'.format(
                survey=EMAIL_COLLECTION_SURVEY_ID, start=startdate,
                end=enddate, page=page, user=user, password=password))

        results = json.loads(response.content)
        total_pages = results['total_pages']
        more_pages = page < total_pages
        emails = emails + [r['[question(13)]'] for r in results['data']]

    return emails


def add_email_to_campaign(email, user, password):
    response = requests.put(
        'https://restapi.surveygizmo.com/v2/survey/{survey}'
        '/surveycampaign/{campaign}/contact?'
        'semailaddress={email}'
        '&user:pass={user}:{password}'.format(
            survey=EXIT_SURVEY_ID, campaign=EXIT_SURVEY_CAMPAIGN_ID,
            email=email, user=user, password=password))

    if response.status_code == 200:
        print 'Added: %s' % email
    else:
        print 'Error adding: %s' % email


if __name__ == '__main__':
    parser = optparse.OptionParser(usage=USAGE)
    parser.add_option('-u', '--username', action='store',
                      dest='username', type='string',
                      help='Surveygizmo username (email address)')
    parser.add_option('-p', '--password', action='store',dest='password',
                      type='string',
                      help='Surveygizmo password')
    parser.add_option('-s', '--start', action='store',
                      dest='start', type='string',
                      default=str(date.today() - timedelta(days=2)),
                      help='(optional) Start date (YYYY-MM-DD). '
                           'Default: 2 days ago')
    parser.add_option('-e', '--end', action='store', dest='end',
                      type='string',
                      default=str(date.today() - timedelta(days=1)),
                      help='(optional) End date (YYYY-MM-DD). '
                           'Default: 1 day ago')
    (options, args) = parser.parse_args()
    (options, args) = parser.parse_args()

    if not options.username or not options.password:
        print 'A required argument is missing.'
        parser.print_help()
        sys.exit(1)

    startdate = datetime.strptime(options.start, '%Y-%m-%d').date()
    enddate = datetime.strptime(options.end, '%Y-%m-%d').date()
    user = options.username
    password = options.password

    print 'Collecting email addresses for %s - %s' % (startdate, enddate)

    emails = get_email_addresses(
        startdate, enddate, user, password)

    print '%s emails collected...' % len(emails)
    for email in emails:
        add_email_to_campaign(email, user, password)
