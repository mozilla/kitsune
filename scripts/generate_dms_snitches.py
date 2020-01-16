#!/usr/bin/env python
import os
import sys

import requests


API_KEY = os.getenv('DMS_API_KEY')
TAGS = os.getenv('DMS_TAGS')
ENVIRONMENT = os.getenv('DMS_ENVIRONMENT')

# Dead Man Snitches
SNITCHES = {
    'SUMO Enqueue Lag Monitor Task': {
        'interval': '15_minute',
        'tags': [],
    },
    'SUMO Send Welcome Emails': {
        'interval': 'hourly',
        'tags': [],
    },
    'SUMO Update Product Details': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Generate Missing Share Links': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Rebuild Kb': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Update Top Contributors': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Update L10n Coverage Metrics': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Calculate Csat Metrics': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Report Employee Answers': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Reindex Users That Contributed Yesterday': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Update Weekly Votes': {
        'interval': 'daily',
        'tags': [],
    },
    # 'SUMO Update Search Ctr Metric': {
    #     'interval': 'daily',
    #     'tags': [],
    # },
    'SUMO Remove Expired Registration Profiles': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Update Contributor Metrics': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Auto Archive Old Questions': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Reindex': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Process Exit Surveys': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Survey Recent Askers': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Clear Expired Auth Tokens': {
        'interval': 'daily',
        'tags': [],
    },
    # 'SUMO Update Visitors Metric': {
    #     'interval': 'daily',
    #     'tags': [],
    # },
    'SUMO Update L10n Metric': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Reload Wiki Traffic Stats': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Cache Most Unhelpful Kb Articles': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Reload Question Traffic Stats': {
        'interval': 'daily',
        'tags': [],
    },
    'SUMO Purge Hashes': {
        'interval': 'weekly',
        'tags': [],
    },
    'SUMO Send Weekly Ready For Review Digest': {
        'interval': 'weekly',
        'tags': [],
    },
    'SUMO Fix Current Revisions': {
        'interval': 'weekly',
        'tags': [],
    },
    'SUMO Cohort Analysis': {
        'interval': 'weekly',
        'tags': [],
    },
    'SUMO Update L10n Contributor Metrics': {
        'interval': 'monthly',
        'tags': [],
    },
}

if not API_KEY:
    print('Provide API key using the DMS_API_KEY environment variable.')
    sys.exit(1)

print('Tags: {}'.format(TAGS))
print('Environment: {}'.format(ENVIRONMENT))
print('Number of snitches: {}'.format(len(SNITCHES)))

if input('Proceed? (y/n) ').lower() == 'y':
    print('Generating snitches:')
    for name, properties in SNITCHES.items():
        properties['name'] = name
        if ENVIRONMENT:
            properties['name'] = '[{}] {}'.format(ENVIRONMENT, name)
        properties['tags'].append(TAGS.split(','))

        print(' - {}'.format(properties['name']))
        requests.post(
            'https://api.deadmanssnitch.com/v1/snitches',
            auth=(API_KEY, ''),
            data=properties,
        )
