from datetime import date

from celery import shared_task
from django.conf import settings
from django.db import connection

from kitsune.dashboards.models import (
    L10N_ACTIVE_CONTRIBUTORS_CODE,
    L10N_ALL_CODE,
    L10N_TOP20_CODE,
    L10N_TOP100_CODE,
    PERIODS,
    WikiDocumentVisits,
    WikiMetric,
)
from kitsune.dashboards.readouts import l10n_overview_rows
from kitsune.products.models import Product
from kitsune.sumo.decorators import skip_if_read_only_mode
from kitsune.sumo.redis_utils import redis_client
from kitsune.wiki.models import Document
from kitsune.wiki.utils import num_active_contributors

HELPFUL_AGGREGATE = "SUM(CASE WHEN limitedvotes.helpful THEN 1 ELSE 0 END)"
UNHELPFUL_AGGREGATE = "SUM(CASE WHEN limitedvotes.helpful THEN 0 ELSE 1 END)"
SQL_UNHELPFUL = f"""
    SELECT doc_id, yes, no
    FROM
        (SELECT wiki_revision.document_id as doc_id,
            {HELPFUL_AGGREGATE} as yes,
            {UNHELPFUL_AGGREGATE} as no
        FROM
            (SELECT *
             FROM wiki_helpfulvote
             WHERE {{}}) as limitedvotes
        INNER JOIN wiki_revision ON
            limitedvotes.revision_id=wiki_revision.id
        INNER JOIN wiki_document ON
            wiki_document.id=wiki_revision.document_id
        WHERE wiki_document.locale='en-US'
        GROUP BY doc_id
        HAVING {UNHELPFUL_AGGREGATE} > {HELPFUL_AGGREGATE}) as calculated
"""
TWO_WEEKS_AGO = "created <= (CURRENT_DATE - 7) AND created >= (CURRENT_DATE - 14)"
PAST_WEEK = "created >= CURRENT_DATE - 7"


@shared_task
@skip_if_read_only_mode
def update_l10n_coverage_metrics() -> None:
    """
    Calculate and store the l10n metrics for each locale/product. The metrics are:
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
        for product in [None, *list(Product.objects.filter(visible=True))]:
            # (Ab)use the l10n_overview_rows helper from the readouts.
            rows = l10n_overview_rows(locale=locale, product=product)

            # % of top 20 articles
            top20 = rows["top-20"]

            try:
                percent = 100.0 * float(top20["numerator"]) / top20["denominator"]
            except ZeroDivisionError:
                percent = 0.0

            WikiMetric.objects.create(
                code=L10N_TOP20_CODE, locale=locale, product=product, date=today, value=percent
            )

            # % of top 100 articles
            top100 = rows["top-100"]

            try:
                percent = 100.0 * float(top100["numerator"]) / top100["denominator"]
            except ZeroDivisionError:
                percent = 0.0

            WikiMetric.objects.create(
                code=L10N_TOP100_CODE,
                locale=locale,
                product=product,
                date=today,
                value=percent,
            )

            # % of all articles
            all_ = rows["all"]
            try:
                percent = 100 * float(all_["numerator"]) / all_["denominator"]
            except ZeroDivisionError:
                percent = 0.0

            WikiMetric.objects.create(
                code=L10N_ALL_CODE, locale=locale, product=product, date=today, value=percent
            )


@shared_task
@skip_if_read_only_mode
def reload_wiki_traffic_stats(verbose: bool = True) -> None:
    for period, _ in PERIODS:
        WikiDocumentVisits.reload_period_from_analytics(period, verbose=verbose)


def _get_old_unhelpful():
    """
    Gets the data from 2 weeks ago and formats it as output so that we can
    get a percent change.
    """

    old_formatted = {}
    with connection.cursor() as cursor:
        cursor.execute(SQL_UNHELPFUL.format(TWO_WEEKS_AGO))
        old_data = cursor.fetchall()

    for data in old_data:
        doc_id = data[0]
        yes = float(data[1])
        no = float(data[2])
        total = yes + no
        if total == 0:
            continue
        old_formatted[doc_id] = {"total": total, "percentage": yes / total}

    return old_formatted


def _get_current_unhelpful(old_formatted):
    """Gets the data for the past week and formats it as return value."""

    final = {}
    with connection.cursor() as cursor:
        cursor.execute(SQL_UNHELPFUL.format(PAST_WEEK))
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
                "total": total,
                "currperc": percentage,
                "diffperc": percentage - old_formatted[doc_id]["percentage"],
            }
        else:
            final[doc_id] = {"total": total, "currperc": percentage, "diffperc": 0.0}

    return final


@shared_task
@skip_if_read_only_mode
def cache_most_unhelpful_kb_articles() -> None:
    """Calculate and save the most unhelpful KB articles in the past two weeks."""

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

    mean_perc = _mean([float(final[key]["currperc"]) for key in list(final.keys())])
    mean_total = _mean([float(final[key]["total"]) for key in list(final.keys())])

    #  TODO: Make this into namedtuples
    sorted_final = [
        (
            key,
            final[key]["total"],
            final[key]["currperc"],
            final[key]["diffperc"],
            _bayes_avg(mean_perc, mean_total, final[key]["currperc"], final[key]["total"]),
        )
        for key in list(final.keys())
    ]
    sorted_final.sort(key=lambda entry: entry[4])  # Sort by Bayesian Avg

    redis = redis_client("helpfulvotes")

    redis.delete(REDIS_KEY)

    max_total = max([b[1] for b in sorted_final])

    for entry in sorted_final:
        doc = Document.objects.get(pk=entry[0])
        redis.rpush(
            REDIS_KEY,
            (
                "{}::{}::{}::{}::{}::{}::{}".format(
                    entry[0],  # Document ID
                    entry[1],  # Total Votes
                    entry[2],  # Current Percentage
                    entry[3],  # Difference in Percentage
                    1 - (entry[1] / max_total),  # Graph Color
                    doc.slug,  # Document slug
                    doc.title,  # Document title
                )
            ),
        )


@shared_task
@skip_if_read_only_mode
def update_l10n_contributor_metrics(day_isoformat: str | None = None) -> None:
    """
    An active contributor is defined as a user that created or reviewed a
    revision in the previous calendar month.
    """
    day = date.today() if day_isoformat is None else date.fromisoformat(day_isoformat)
    first_of_month = date(day.year, day.month, 1)
    if day.month == 1:
        previous_first_of_month = date(day.year - 1, 12, 1)
    else:
        previous_first_of_month = date(day.year, day.month - 1, 1)

    # Loop through all locales.
    for locale in settings.SUMO_LANGUAGES:
        # Loop through all enabled products, including None (really All).
        for product in [None, *list(Product.objects.filter(visible=True))]:
            num = num_active_contributors(
                from_date=previous_first_of_month,
                to_date=first_of_month,
                locale=locale,
                product=product,
            )

            WikiMetric.objects.create(
                code=L10N_ACTIVE_CONTRIBUTORS_CODE,
                locale=locale,
                product=product,
                date=previous_first_of_month,
                value=num,
            )
