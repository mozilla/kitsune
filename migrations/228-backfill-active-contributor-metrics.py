# -*- coding: utf-8 -*-
from datetime import date

from kitsune.dashboards.cron import update_l10n_contributor_metrics


def run():
    # Run for ever first of every month this year.
    today = date.today()
    year = today.year
    month = today.month
    i = 1

    while i <= month:
        day = date(year, i, 1)
        update_l10n_contributor_metrics(day)
        i += 1
