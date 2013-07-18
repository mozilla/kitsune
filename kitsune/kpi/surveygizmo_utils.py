import json
from datetime import timedelta

from django.conf import settings

import requests

EMAIL_COLLECTION_SURVEY_ID = 1002970
EXIT_SURVEY_ID = 991425
EXIT_SURVEY_CAMPAIGN_ID = 878533


def get_email_addresses(startdate, enddate):
    """Get the email addresses collected between startdate and enddate."""
    user = settings.SURVEYGIZMO_USER
    password = settings.SURVEYGIZMO_PASSWORD
    emails = []
    page = 1
    more_pages = True

    while more_pages:
        response = requests.get(
            'https://restapi.surveygizmo.com/v2/survey/{survey}'
            '/surveyresponse?'
            'filter[field][0]=datesubmitted'
            '&filter[operator][0]=>=&filter[value][0]={start}+0:0:0'
            'filter[field][1]=datesubmitted'
            '&filter[operator][1]=<&filter[value][1]={end}+0:0:0'
            '&filter[field][2]=status&filter[operator][2]=='
            '&filter[value][2]=Complete'
            '&resultsperpage=500'
            '&page={page}'
            '&user:pass={user}:{password}'.format(
                survey=EMAIL_COLLECTION_SURVEY_ID, start=startdate,
                end=enddate, page=page, user=user, password=password),
            timeout=300)

        results = json.loads(response.content)
        total_pages = results['total_pages']
        more_pages = page < total_pages
        emails = emails + [r['[question(13)]'] for r in results['data']]
        page += 1

    return emails


def add_email_to_campaign(email):
    """Add email to the exit survey campaign."""
    user = settings.SURVEYGIZMO_USER
    password = settings.SURVEYGIZMO_PASSWORD

    try:
        requests.put(
            'https://restapi.surveygizmo.com/v2/survey/{survey}'
            '/surveycampaign/{campaign}/contact?'
            'semailaddress={email}'
            '&user:pass={user}:{password}'.format(
                survey=EXIT_SURVEY_ID, campaign=EXIT_SURVEY_CAMPAIGN_ID,
                email=email, user=user, password=password),
            timeout=30)
    except requests.exceptions.Timeout:
        print 'Timedout adding: %s' % email


def get_exit_survey_results(date):
    """Collect and aggregate the exit survey results for the date."""
    user = settings.SURVEYGIZMO_USER
    password = settings.SURVEYGIZMO_PASSWORD
    answers = []
    page = 1
    more_pages = True

    while more_pages:
        response = requests.get(
            'https://restapi.surveygizmo.com/v2/survey/{survey}'
            '/surveyresponse?'
            'filter[field][0]=datesubmitted'
            '&filter[operator][0]=>=&filter[value][0]={start}+0:0:0'
            '&filter[field][1]=datesubmitted'
            '&filter[operator][1]=<&filter[value][1]={end}+0:0:0'
            '&filter[field][2]=status&filter[operator][2]=='
            '&filter[value][2]=Complete'
            '&resultsperpage=500'
            '&page={page}'
            '&user:pass={user}:{password}'.format(
                survey=EXIT_SURVEY_ID,
                start=date,
                end=date + timedelta(days=1),
                page=page,
                user=user,
                password=password),
            timeout=300)

        results = json.loads(response.content)
        total_pages = results['total_pages']
        more_pages = page < total_pages
        answers = answers + [r['[question(2)]'] for r in results['data']]
        page += 1

    # Aggregate results.
    summary = {
        'yes': 0,
        'no': 0,
        'dont-know': 0,
    }

    for answer in answers:
        lower_stripped = answer.lower().strip()
        if lower_stripped in ['no', 'yes']:
            summary[lower_stripped] += 1
        else:
            summary['dont-know'] += 1

    return summary
