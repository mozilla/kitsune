from datetime import date, timedelta

from django.conf import settings
from django.db import connection

import cronjobs

from kitsune.dashboards.models import (
    PERIODS, WikiDocumentVisits, WikiMetric, L10N_TOP20_CODE, L10N_ALL_CODE,
    L10N_ACTIVE_CONTRIBUTORS_CODE)
from kitsune.dashboards.readouts import overview_rows
from kitsune.products.models import Product
from kitsune.sumo.redis_utils import redis_client
from kitsune.wiki.models import Document
from kitsune.wiki.utils import num_active_contributors


@cronjobs.register
def reload_wiki_traffic_stats():
    if settings.STAGE:
        print ('Skipped reload_wiki_traffic_stats(). '
               'Set settings.STAGE to False to run it for real.')
        return

    for period, _ in PERIODS:
        WikiDocumentVisits.reload_period_from_analytics(period)


@cronjobs.register
def update_l10n_coverage_metrics():
    """Calculate and store the l10n metrics for each locale/product.

    The metrics are:
    * Percent localized of top 20 articles
    * Percent localized of all articles
    """
    today = date.today()

    # Loop through all locales.
    for locale in settings.SUMO_LANGUAGES:

        # Skip en-US, it is always 100% localized.
        if locale == settings.WIKI_DEFAULT_LANGUAGE:
            continue

        # Loop through all enabled products, including None (really All).
        for product in [None] + list(Product.objects.filter(visible=True)):

            # (Ab)use the overview_rows helper from the readouts.
            rows = overview_rows(locale=locale, product=product)

            # % of top 20 articles
            top20 = rows['most-visited']
            percent = 100.0 * float(top20['numerator']) / top20['denominator']
            WikiMetric.objects.create(
                code=L10N_TOP20_CODE,
                locale=locale,
                product=product,
                date=today,
                value=percent)

            # % of all articles
            all_ = rows['all']
            percent = 100.0 * float(all_['numerator']) / all_['denominator']
            WikiMetric.objects.create(
                code=L10N_ALL_CODE,
                locale=locale,
                product=product,
                date=today,
                value=percent)


@cronjobs.register
def update_l10n_contributor_metrics(day=None):
    """Update the number of active contributors for each locale/product.

    An active contributor is defined as a user that created or reviewed a
    revision in the last 30 days.
    """
    if day is None:
        day = date.today()
    thirty_days_back = day - timedelta(days=30)

    # Loop through all locales.
    for locale in settings.SUMO_LANGUAGES:

        # Loop through all enabled products, including None (really All).
        for product in [None] + list(Product.objects.filter(visible=True)):

            num = num_active_contributors(
                from_date=thirty_days_back,
                to_date=day,
                locale=locale,
                product=product)

            WikiMetric.objects.create(
                code=L10N_ACTIVE_CONTRIBUTORS_CODE,
                locale=locale,
                product=product,
                date=day,
                value=num)


def _get_old_unhelpful():
    """
    Gets the data from 2 weeks ago and formats it as output so that we can
    get a percent change.
    """

    old_formatted = {}
    cursor = connection.cursor()

    cursor.execute(
        """SELECT doc_id, yes, no
        FROM
            (SELECT wiki_revision.document_id as doc_id,
                SUM(limitedvotes.helpful) as yes,
                SUM(NOT(limitedvotes.helpful)) as no
            FROM
                (SELECT * FROM wiki_helpfulvote
                    WHERE created <= DATE_SUB(CURDATE(), INTERVAL 1 WEEK)
                    AND created >= DATE_SUB(DATE_SUB(CURDATE(),
                        INTERVAL 1 WEEK), INTERVAL 1 WEEK)
                ) as limitedvotes
            INNER JOIN wiki_revision ON
                limitedvotes.revision_id=wiki_revision.id
            INNER JOIN wiki_document ON
                wiki_document.id=wiki_revision.document_id
            WHERE wiki_document.locale="en-US"
            GROUP BY doc_id
            HAVING no > yes
            ) as calculated""")

    old_data = cursor.fetchall()

    for data in old_data:
        doc_id = data[0]
        yes = float(data[1])
        no = float(data[2])
        total = yes + no
        if total == 0:
            continue
        old_formatted[doc_id] = {'total': total,
                                 'percentage': yes / total}

    return old_formatted


def _get_current_unhelpful(old_formatted):
    """Gets the data for the past week and formats it as return value."""

    final = {}
    cursor = connection.cursor()

    cursor.execute(
        """SELECT doc_id, yes, no
        FROM
            (SELECT wiki_revision.document_id as doc_id,
                SUM(limitedvotes.helpful) as yes,
                SUM(NOT(limitedvotes.helpful)) as no
            FROM
                (SELECT * FROM wiki_helpfulvote
                    WHERE created >= DATE_SUB(CURDATE(), INTERVAL 1 WEEK)
                ) as limitedvotes
            INNER JOIN wiki_revision ON
                limitedvotes.revision_id=wiki_revision.id
            INNER JOIN wiki_document ON
                wiki_document.id=wiki_revision.document_id
            WHERE wiki_document.locale="en-US"
            GROUP BY doc_id
            HAVING no > yes
            ) as calculated""")

    current_data = cursor.fetchall()

    for data in current_data:
        doc_id = data[0]
        yes = float(data[1])
        no = float(data[2])
        total = yes + no
        if total == 0:
            continue
        percentage = yes / total
        if doc_id in old_formatted:
            final[doc_id] = {
                'total': total,
                'currperc': percentage,
                'diffperc': percentage - old_formatted[doc_id]['percentage']
            }
        else:
            final[doc_id] = {
                'total': total,
                'currperc': percentage,
                'diffperc': 0.0
            }

    return final


@cronjobs.register
def cache_most_unhelpful_kb_articles():
    """Calculate and save the most unhelpful KB articles in the past month."""

    REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY

    old_formatted = _get_old_unhelpful()
    final = _get_current_unhelpful(old_formatted)

    if final == {}:
        return

    def _mean(vals):
        """Argument: List of floats"""
        if len(vals) == 0:
            return None
        return sum(vals) / len(vals)

    def _bayes_avg(C, m, R, v):
        # Bayesian Average
        # C = mean vote, v = number of votes,
        # R = mean rating, m = minimum votes to list in topranked
        return (C * m + R * v) / (m + v)

    mean_perc = _mean([float(final[key]['currperc']) for key in final.keys()])
    mean_total = _mean([float(final[key]['total']) for key in final.keys()])

    #  TODO: Make this into namedtuples
    sorted_final = [(key,
                     final[key]['total'],
                     final[key]['currperc'],
                     final[key]['diffperc'],
                     _bayes_avg(mean_perc, mean_total,
                                final[key]['currperc'],
                                final[key]['total']))
                    for key in final.keys()]
    sorted_final.sort(key=lambda entry: entry[4])  # Sort by Bayesian Avg

    redis = redis_client('helpfulvotes')

    redis.delete(REDIS_KEY)

    max_total = max([b[1] for b in sorted_final])

    for entry in sorted_final:
        doc = Document.objects.get(pk=entry[0])
        redis.rpush(REDIS_KEY, (u'%s::%s::%s::%s::%s::%s::%s' %
                                  (entry[0],  # Document ID
                                   entry[1],  # Total Votes
                                   entry[2],  # Current Percentage
                                   entry[3],  # Difference in Percentage
                                   1 - (entry[1] / max_total),  # Graph Color
                                   doc.slug,  # Document slug
                                   doc.title)))  # Document title
