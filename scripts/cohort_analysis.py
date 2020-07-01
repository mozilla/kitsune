#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Groups users into monthly cohorts, and analyzes drop off rate for each group.

Run this script like `./manage.py runscript cohort_analysis`.
"""
from datetime import datetime
from datetime import timedelta
from traceback import print_exc

from tabulate import tabulate

from kitsune.questions.models import Answer
from kitsune.wiki.models import Revision


def run():
    try:
        run_()
    except Exception:
        print_exc()
        raise


def run_():
    now = datetime.now()
    boundaries = [datetime(now.year, now.month, 1)]
    for _ in range(12):
        first_day_of_previous_month = (boundaries[-1] - timedelta(days=1)).replace(day=1)
        boundaries.append(first_day_of_previous_month)
    boundaries.reverse()
    ranges = list(zip(boundaries[:-1], boundaries[1:]))

    reports = [
        ('L10n', Revision.objects.exclude(document__locale='en-US')),
        ('KB', Revision.objects.filter(document__locale='en-US')),
        ('Questions', Answer.objects.all())
    ]

    for title, queryset in reports:
        data = report_for(queryset, ranges)
        headers = [title] + [s.strftime('%b') for s, _ in ranges]
        print(tabulate(data, headers=headers))
        print()


def count_contributors_in_range(queryset, users, date_range):
    """Of the group ``users``, count how many made a contribution in ``date_range``."""
    start, end = date_range
    users = set(o.creator for o in
                queryset.filter(creator__in=users, created__gte=start, created__lt=end))
    return len(users)


def get_cohort(queryset, date_range):
    start, end = date_range
    contributions_in_range = queryset.filter(created__gte=start, created__lt=end)
    potential_users = set(cont.creator for cont in contributions_in_range)

    def is_in_cohort(u):
        first_contrib = queryset.filter(creator=u).order_by('id')[0]
        return start <= first_contrib.created < end

    return list(filter(is_in_cohort, potential_users))


def report_for(queryset, ranges):
    for i, cohort_range in enumerate(ranges):
        cohort_users = get_cohort(queryset, cohort_range)
        start, end = cohort_range
        data = []

        data.append(start.strftime('%b %Y'))
        # Fill months before the cohort started
        for _ in range(i):
            data.append(None)
        data.append(len(cohort_users))

        for return_range in ranges[i + 1:]:
            returned = count_contributors_in_range(queryset, cohort_users, return_range)
            data.append(returned)

        yield data
