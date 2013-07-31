# -*- coding: utf-8 -*-
from datetime import date

from kitsune.dashboards.cron import update_l10n_contributor_metrics


def run():
    # Run for every first of every month for the past year.
    today = date.today()
    current_year = today.year
    current_month = today.month

    year = current_year - 1
    month = current_month - 1

    while year < current_year or month <= current_month:
        day = date(year, month, 1)
        update_l10n_contributor_metrics(day)

        month += 1
        if month > 12:
            month = 1
            year += 1
