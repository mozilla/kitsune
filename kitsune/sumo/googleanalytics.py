import datetime
import json
import logging

from django.conf import settings
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    FilterExpressionList,
    Metric,
    OrderBy,
    RunReportRequest,
)
from google.api_core.retry import Retry
from google.oauth2 import service_account

from kitsune.dashboards import LAST_30_DAYS, LAST_7_DAYS, LAST_90_DAYS, LAST_YEAR


log = logging.getLogger("k.googleanalytics")


# The default Retry instance retries on all transient errors.
retry_on_transient_errors = Retry()


PERIOD_TO_DAYS_AGO = {
    LAST_7_DAYS: "7daysAgo",
    LAST_30_DAYS: "30daysAgo",
    LAST_90_DAYS: "90daysAgo",
    LAST_YEAR: "365daysAgo",
}


def get_client():
    """
    Returns an authenticated client for making requests to the GA4 data API.
    """
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(settings.GA_KEY),
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    return BetaAnalyticsDataClient(credentials=credentials)


def run_report(date_range, create_report_request, limit=10000, verbose=False):
    """
    A generator that yields results from GA4 data API using the given
    "create_report_request" function to create RunReportRequest instances,
    and limited to the given date range. It handles paging in chunks sized
    by the provided "limit" until all of the requested data has been received.
    """
    if (limit <= 0) or (limit > 10000):
        # The maximum number of rows that the GA4 data API will return is 10K.
        limit = 10000

    offset = 0
    response = None

    client = get_client()

    if verbose:
        log.info(
            f"Running GA4 report from {date_range.start_date} to {date_range.end_date}"
            f' using "{create_report_request.__name__}"...'
        )

    while (response is None) or (offset < response.row_count):
        request = create_report_request(date_range, offset=offset, limit=limit)
        if verbose:
            log.info(f"Fetching rows {offset} to {offset + limit}...")
        response = client.run_report(request, retry=retry_on_transient_errors)
        if verbose:
            log.info(f"Received {len(response.rows)} rows.")
        for row in response.rows:
            yield row
        offset += limit


def create_page_view_report_request(content_group, date_range, offset=0, limit=10000):
    """
    Create a RunReportRequest instance for a report of the page views by URL path, but
    only for page views of the given content group, and limited to the results with the
    given offset and limit.
    """
    dimensions = [Dimension(name="pagePath")]
    if content_group == "kb-article":
        dimensions.append(Dimension(name="customEvent:article_locale"))

    return RunReportRequest(
        property=f"properties/{settings.GA_PROPERTY_ID}",
        dimensions=dimensions,
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            and_group=FilterExpressionList(
                expressions=[
                    FilterExpression(
                        filter=Filter(
                            field_name="eventName",
                            string_filter=Filter.StringFilter(
                                value="page_view", match_type=Filter.StringFilter.MatchType.EXACT
                            ),
                        )
                    ),
                    FilterExpression(
                        filter=Filter(
                            field_name="contentGroup",
                            string_filter=Filter.StringFilter(
                                value=content_group, match_type=Filter.StringFilter.MatchType.EXACT
                            ),
                        )
                    ),
                ]
            )
        ),
        limit=limit,
        offset=offset,
    )


def create_article_report_request(date_range, offset=0, limit=10000):
    """
    Create a RunReportRequest instance for a report of KB article page views by URL path
    within the given date range, and limited to the results with the given offset and limit.
    """
    return create_page_view_report_request("kb-article", date_range, offset=offset, limit=limit)


def create_question_report_request(date_range, offset=0, limit=10000):
    """
    Create a RunReportRequest instance for a report of question page views by question URL
    path within the given date range, and limited to the results with the given offset and
    limit.
    """
    return create_page_view_report_request(
        "support-forum-question-details", date_range, offset=offset, limit=limit
    )


def create_visitors_by_date_report_request(date_range, offset=0, limit=10000):
    """
    Create a RunReportRequest instance for a report of the total number of unique users for
    each day in the given date range, and limited to the results with the given offset and
    limit.
    """
    return RunReportRequest(
        property=f"properties/{settings.GA_PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="totalUsers")],
        date_ranges=[date_range],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=False)],
        limit=limit,
        offset=offset,
    )


def create_visitors_by_locale_report_request(date_range, offset=0, limit=10000):
    """
    Create a RunReportRequest instance for a report of the total number of unique users for
    each locale within the given date range, and limited to the results with the given offset
    and limit.
    """
    return RunReportRequest(
        property=f"properties/{settings.GA_PROPERTY_ID}",
        dimensions=[Dimension(name="customEvent:locale")],
        metrics=[Metric(name="totalUsers")],
        date_ranges=[date_range],
        limit=limit,
        offset=offset,
    )


def create_search_report_request(date_range, offset=0, limit=10000):
    """
    Create a RunReportRequest instance for a report of the total number of search events for
    each day in the given date range, and limited to the results with the given offset and
    limit.
    """
    return RunReportRequest(
        property=f"properties/{settings.GA_PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    value="search", match_type=Filter.StringFilter.MatchType.EXACT
                ),
            )
        ),
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=False)],
        limit=limit,
        offset=offset,
    )


def create_click_search_result_report_request(date_range, offset=0, limit=10000):
    """
    Create a RunReportRequest instance for a report of the total number of clicks on search
    results for each day in the given date range, and limited to the results with the given
    offset and limit.
    """
    return RunReportRequest(
        property=f"properties/{settings.GA_PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[date_range],
        dimension_filter=FilterExpression(
            and_group=FilterExpressionList(
                expressions=[
                    FilterExpression(
                        filter=Filter(
                            field_name="eventName",
                            string_filter=Filter.StringFilter(
                                value="link_click", match_type=Filter.StringFilter.MatchType.EXACT
                            ),
                        )
                    ),
                    FilterExpression(
                        filter=Filter(
                            field_name="customEvent:link_name",
                            string_filter=Filter.StringFilter(
                                value="search-result.",
                                match_type=Filter.StringFilter.MatchType.BEGINS_WITH,
                            ),
                        )
                    ),
                ]
            )
        ),
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=False)],
        limit=limit,
        offset=offset,
    )


def visitors(start_date, end_date, verbose=False):
    """
    Generator that returns a tuple of (date, total_users), where date is an instance
    of datetime.date, and "total_users" is the total number of unique users for each
    day within the given start and end dates. The results are yielded in order from
    the start date to the end date.
    """
    date_range = DateRange(start_date=str(start_date), end_date=str(end_date))

    next_date_to_yield = start_date
    for row in run_report(date_range, create_visitors_by_date_report_request, verbose=verbose):
        # The GA4 data API returns dates in the string format of "YYYYMMDD",
        # which the datetime.date.fromisoformat method accepts.
        date = datetime.date.fromisoformat(row.dimension_values[0].value)
        total_users = int(row.metric_values[0].value)

        # Dates with zero users will not be included in the GA4 results, so we
        # need to fill-in any gaps day-by-day with reports of zero total users.
        while next_date_to_yield < date:
            yield (next_date_to_yield, 0)
            next_date_to_yield += datetime.timedelta(days=1)

        yield (date, total_users)

        # If there are more dates to yield, we expect the next one to be a day
        # after the one we just yielded.
        next_date_to_yield = date + datetime.timedelta(days=1)


def visitors_by_locale(start_date, end_date, verbose=False):
    """
    Returns a dictionary with the total unique users for each locale within the given
    start and end dates.
    """
    date_range = DateRange(start_date=str(start_date), end_date=str(end_date))

    results = {}
    for row in run_report(date_range, create_visitors_by_locale_report_request, verbose=verbose):
        locale = row.dimension_values[0].value
        total_users = int(row.metric_values[0].value)
        results[locale] = total_users
    return results


def pageviews_by_document(period, verbose=False):
    """
    A generator that yields tuples of ((locale, slug), num_page_views) for every
    KB article with one or more page views within the given period.
    """
    date_range = DateRange(start_date=PERIOD_TO_DAYS_AGO[period], end_date="today")

    for row in run_report(date_range, create_article_report_request, verbose=verbose):
        path = row.dimension_values[0].value
        article_locale = row.dimension_values[1].value
        # The path should be a KB article path without any query parameters, but in reality
        # we've seen that it can sometimes be "/". If the URL path for KB articles changes,
        # we'll need to continue to support the previous URL structure for a year -- the
        # longest period of time we look backwards -- as well as the new URL structure.
        # Current URL structure: /{locale}/kb/{slug}
        try:
            num_page_views = int(row.metric_values[0].value)
            locale, slug = path.strip("/").split("/kb/")
        except ValueError:
            continue
        yield ((article_locale if article_locale else locale, slug), num_page_views)


def pageviews_by_question(period=LAST_YEAR, verbose=False):
    """
    A generator that yields tuples of (question_id, num_page_views) for every
    question with one or more page views within the given period.
    """
    date_range = DateRange(start_date=PERIOD_TO_DAYS_AGO[period], end_date="today")

    for row in run_report(date_range, create_question_report_request, verbose=verbose):
        path = row.dimension_values[0].value
        # The path should be a question path without any query parameters, but in reality
        # we've seen that it can sometimes be "/". If the URL path for questions changes,
        # we'll need to continue to support the previous URL structure for a year -- the
        # longest period of time we look backwards -- as well as the new URL structure.
        # Current URL structure: /{locale}/questions/{question_id}
        try:
            num_page_views = int(row.metric_values[0].value)
            locale, question_id = path.strip("/").split("/questions/")
            question_id = int(question_id)
        except ValueError:
            continue
        yield (question_id, num_page_views)


def search_clicks_and_impressions(start_date, end_date, verbose=False):
    """
    A generator that yields tuples of (date, total_clicks, total_searches) for each
    day within the given start and end dates. The date is an instance of datetime.date,
    "total_clicks" is the total number of clicks on search results on that date, and the
    "total_searches" is the total number of searches performed on that date.
    """
    date_range = DateRange(start_date=str(start_date), end_date=str(end_date))

    searches_by_date = {}
    for row in run_report(date_range, create_search_report_request, verbose=verbose):
        date = row.dimension_values[0].value
        total_searches = int(row.metric_values[0].value)
        searches_by_date[date] = total_searches

    search_result_clicks_by_date = {}
    for row in run_report(date_range, create_click_search_result_report_request, verbose=verbose):
        date = row.dimension_values[0].value
        total_clicks = int(row.metric_values[0].value)
        search_result_clicks_by_date[date] = total_clicks

    date = start_date
    while date <= end_date:
        ga_date_key = date.strftime("%Y%m%d")
        total_searches = searches_by_date.get(ga_date_key, 0)
        total_clicks = search_result_clicks_by_date.get(ga_date_key, 0)
        yield (date, total_clicks, total_searches)
        date += datetime.timedelta(days=1)
