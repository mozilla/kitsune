import json
from datetime import timedelta

from django.conf import settings

import requests


SURVEYS = {
    'general': {  # This is for users browsing the KB and navigation pages.
        'email_collection_survey_id': 1002970,
        'exit_survey_id': 991425,
        'exit_survey_campaign_id': 878533,
    },
    'questions': {  # This is for users that are browsing questions.
        'email_collection_survey_id': 1717268,
        'exit_survey_id': 1724445,
        'exit_survey_campaign_id': 1687339,
    },
    'askers': {  # This is for users that asked a question 2 days ago.
        'exit_survey_id': 1817790,
        'exit_survey_campaign_id': 1876443,
    }
}


def get_email_addresses(survey, startdate, enddate):
    """Get the email addresses collected between startdate and enddate."""
    user = settings.SURVEYGIZMO_USER
    password = settings.SURVEYGIZMO_PASSWORD
    emails = []
    page = 1
    more_pages = True
    survey_id = SURVEYS[survey]['email_collection_survey_id']

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
                survey=survey_id, start=startdate,
                end=enddate, page=page, user=user, password=password),
            timeout=300)

        results = json.loads(response.content)
        total_pages = results['total_pages']
        more_pages = page < total_pages
        emails = emails + [r['[question(13)]'] for r in results['data']]
        page += 1

    return emails


def add_email_to_campaign(survey, email):
    """Add email to the exit survey campaign."""
    user = settings.SURVEYGIZMO_USER
    password = settings.SURVEYGIZMO_PASSWORD

    survey_id = SURVEYS[survey]['exit_survey_id']
    campaign_id = SURVEYS[survey]['exit_survey_campaign_id']

    try:
        requests.put(
            'https://restapi.surveygizmo.com/v2/survey/{survey}'
            '/surveycampaign/{campaign}/contact?'
            'semailaddress={email}'
            '&user:pass={user}:{password}'.format(
                survey=survey_id, campaign=campaign_id,
                email=email, user=user, password=password),
            timeout=30)
    except requests.exceptions.Timeout:
        print 'Timedout adding: %s' % email


def get_exit_survey_results(survey, date):
    """Collect and aggregate the exit survey results for the date."""
    user = settings.SURVEYGIZMO_USER
    password = settings.SURVEYGIZMO_PASSWORD
    answers = []
    page = 1
    more_pages = True
    survey_id = SURVEYS[survey]['exit_survey_id']

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
                survey=survey_id,
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
