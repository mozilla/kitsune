from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth.models import User

from kitsune.customercare.models import ReplyMetricsMappingType
from kitsune.products.models import Product
from kitsune.questions.models import AnswerMetricsMappingType
from kitsune.search.es_utils import F
from kitsune.wiki.models import RevisionMetricsMappingType


def top_contributors_questions(
    start=None, end=None, locale=None, product=None, count=10):
    """Get the top Support Forum contributors."""
    # Get the user ids and contribution count of the top contributors.
    query = (AnswerMetricsMappingType
        .search()
        .facet('creator_id', filtered=True, size=count))

    query = _apply_filters(query, start, end, locale, product)

    return _get_creator_counts(query)


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

    return _get_creator_counts(query)


def top_contributors_aoa(start=None, end=None, locale=None, count=10):
    """Get the top Army of Awesome contributors."""
    # Get the user ids and contribution count of the top contributors.
    query = (ReplyMetricsMappingType
        .search()
        .facet('creator_id', filtered=True, size=count))

    # twitter only does language
    locale = locale.split('-')[0] if locale else None

    query = _apply_filters(query, start, end, locale)

    return _get_creator_counts(query)


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


def _get_creator_counts(query):
    """Get the list of top contributors with the contribution count."""
    creator_counts = query.facet_counts()['creator_id']['terms']

    # Grab all the users from the DB in one query.
    user_ids = [x['term'] for x in creator_counts]
    users = User.objects.filter(id__in=user_ids).select_related('profile')

    # Create a {<user_id>: <user>,...} dict for convenience.
    user_lookup = {}
    for user in users:
        user_lookup[user.id] = user

    # Add the user to each dict in the creator_counts array.
    for item in creator_counts:
        item['user'] = user_lookup[item['term']]

    return creator_counts
