from datetime import datetime, date, timedelta
from django.conf import settings
from django.contrib.auth.models import User

from kitsune.customercare.models import ReplyMetricsMappingType
from kitsune.products.models import Product
from kitsune.questions.models import AnswerMetricsMappingType
from kitsune.search.es_utils import F
from kitsune.users.models import UserMappingType
from kitsune.wiki.models import RevisionMetricsMappingType


def top_contributors_questions(
    start=None, end=None, locale=None, product=None, count=10):
    """Get the top Support Forum contributors."""
    # Get the user ids and contribution count of the top contributors.
    query = (AnswerMetricsMappingType
        .search()
        .facet('creator_id', filtered=True, size=count))

    # Adding answer to your own question, isn't a contribution.
    query = query.filter(by_asker=False)

    query = _apply_filters(query, start, end, locale, product)

    return _get_creator_counts(query, count)


def top_contributors_kb(start=None, end=None, product=None, count=10):
    """Get the top KB editors (locale='en-US')."""
    return top_contributors_l10n(
        start, end, settings.WIKI_DEFAULT_LANGUAGE, product, count)


def top_contributors_l10n(
    start=None, end=None, locale=None, product=None, count=10):
    """Get the top l10n contributors for the KB."""
    # Get the user ids and contribution count of the top contributors.
    query = (RevisionMetricsMappingType
        .search()
        .facet('creator_id', filtered=True, size=count))

    if locale is None:
        # If there is no locale specified, exlude en-US only. The rest are
        # l10n.
        query = query.filter(~F(locale=settings.WIKI_DEFAULT_LANGUAGE))

    query = _apply_filters(query, start, end, locale, product)

    return _get_creator_counts(query, count)


def top_contributors_aoa(start=None, end=None, locale=None, count=10):
    """Get the top Army of Awesome contributors."""
    # Get the user ids and contribution count of the top contributors.
    query = (ReplyMetricsMappingType
        .search()
        .facet('creator_id', filtered=True, size=count))

    # twitter only does language
    locale = locale.split('-')[0] if locale else None

    query = _apply_filters(query, start, end, locale)

    return _get_creator_counts(query, count)


def _apply_filters(query, start, end, locale=None, product=None):
    """Apply the date and locale filters to the EU query."""
    if start is None:
        # By default we go back 90 days.
        start = date.today() - timedelta(days=90)
    query = query.filter(created__gte=start)

    if end:
        # If no end is specified, we don't need to filter by it.
        query = query.filter(created__lt=end)

    if locale:
        query = query.filter(locale=locale)

    if product:
        if isinstance(product, Product):
            product = product.slug
        query = query.filter(product=product)

    return query


def _get_creator_counts(query, count):
    """Get the list of top contributors with the contribution count."""
    creator_counts = query.facet_counts()['creator_id']['terms']

    # Grab all the users from the user index in ES.
    user_ids = [x['term'] for x in creator_counts]
    results = (UserMappingType
        .search()
        .filter(id__in=user_ids)
        .values_dict('id', 'username', 'display_name', 'avatar',
                     'twitter_usernames', 'last_contribution_date'))[:count]
    results = UserMappingType.reshape(results)

    # Calculate days since last activity and
    # create a {<user_id>: <user>,...} dict for convenience.
    user_lookup = {}
    for r in results:
        lcd = r.get('last_contribution_date', None)
        if lcd:
            delta = datetime.now() - lcd
            r['days_since_last_activity'] = delta.days
        else:
            r['days_since_last_activity'] = None

        user_lookup[r['id']] = r

    # Add the user to each dict in the creator_counts array.
    for item in creator_counts:
        item['user'] = user_lookup.get(item['term'], None)

    return [item for item in creator_counts if item['user'] != None]
