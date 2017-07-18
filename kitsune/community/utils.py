from datetime import datetime, date, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

from kitsune.customercare.models import ReplyMetricsMappingType
from kitsune.products.models import Product
from kitsune.questions.models import AnswerMetricsMappingType
from kitsune.search.es_utils import F
from kitsune.users.models import User
from kitsune.users.templatetags.jinja_helpers import profile_avatar
from kitsune.wiki.models import RevisionMetricsMappingType


# This should be higher than the max number of questions, revisions or tweets.
# There isn't a way to tell ES to just return everything.
HUGE_NUMBER = 1500000


def top_contributors_questions(start=None, end=None, locale=None, product=None,
                               count=10, page=1, use_cache=True):
    """Get the top Support Forum contributors."""
    # Get the user ids and contribution count of the top contributors.

    if use_cache:
        cache_key = u'top_contributors_questions_{}_{}_{}_{}_{}_{}'.format(start, end, locale,
                                                                           product, count, page)
        cached = cache.get(cache_key, None)
        if cached:
            return cached

    query = AnswerMetricsMappingType.search()

    # Adding answer to your own question, isn't a contribution.
    query = query.filter(by_asker=False)
    query = _apply_filters(query, start, end, locale, product)

    answers = [q.id for q in query.all()[:HUGE_NUMBER]]
    users = (User.objects
             .filter(answers__in=answers)
             .annotate(query_count=Count('answers'))
             .order_by('-query_count'))

    counts = _get_creator_counts(users, count, page)
    if use_cache:
        cache.set(cache_key, counts, 60*15)  # 15 minutes
    return counts


def top_contributors_kb(start=None, end=None, product=None, count=10, page=1, use_cache=True):
    """Get the top KB editors (locale='en-US')."""
    return top_contributors_l10n(
        start, end, settings.WIKI_DEFAULT_LANGUAGE, product, count, use_cache)


def top_contributors_l10n(start=None, end=None, locale=None, product=None,
                          count=10, page=1, use_cache=True):
    """Get the top l10n contributors for the KB."""

    if use_cache:
        cache_key = u'top_contributors_l10n_{}_{}_{}_{}_{}_{}'.format(start, end, locale,
                                                                      product, count, page)
        cached = cache.get(cache_key, None)
        if cached:
            return cached

    # Get the user ids and contribution count of the top contributors.
    query = RevisionMetricsMappingType.search()

    if locale is None:
        # If there is no locale specified, exclude en-US only. The rest are
        # l10n.
        query = query.filter(~F(locale=settings.WIKI_DEFAULT_LANGUAGE))

    query = _apply_filters(query, start, end, locale, product)
    revisions = [q.id for q in query.all()[:HUGE_NUMBER]]
    users = (User.objects
             .filter(created_revisions__in=revisions)
             .annotate(query_count=Count('created_revisions'))
             .order_by('-query_count'))

    counts = _get_creator_counts(users, count, page)
    if use_cache:
        cache.set(cache_key, counts, 60*15)  # 15 minutes
    return counts


def top_contributors_aoa(start=None, end=None, locale=None, count=10, page=1, use_cache=True):
    """Get the top Army of Awesome contributors."""

    if use_cache:
        cache_key = u'top_contributors_l10n_{}_{}_{}_{}_{}'.format(start, end, locale, count, page)
        cached = cache.get(cache_key, None)

        if cached:
            return cached

    # Get the user ids and contribution count of the top contributors.
    query = ReplyMetricsMappingType.search()

    # twitter only does language
    locale = locale.split('-')[0] if locale else None

    query = _apply_filters(query, start, end, locale)
    tweets = [q.id for q in query.all()[:HUGE_NUMBER]]
    users = (User.objects
             .filter(tweet_replies__in=tweets)
             .annotate(query_count=Count('tweet_replies'))
             .order_by('-query_count'))

    counts = _get_creator_counts(users, count, page)
    if use_cache:
        cache.set(cache_key, counts, 60*15)  # 15 minutes
    return counts


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


def _get_creator_counts(query, count, page):
    total = query.count()
    results = []
    now = datetime.now()
    for user in query[((page - 1) * count):(page * count)]:
        last_contribution_date = user.profile.last_contribution_date
        days_since_last_activity = None
        if last_contribution_date:
            days_since_last_activity = now - last_contribution_date

        data = {
            'count': user.query_count,
            'term': user.id,
            'user': {
                'id': user.id,
                'username': user.username,
                'display_name': user.profile.display_name,
                'avatar': profile_avatar(user, size=120),
                'twitter_usernames': user.profile.twitter_usernames,
                'last_contribution_date': last_contribution_date,
                'days_since_last_activity': days_since_last_activity,
            }
        }
        results.append(data)

    return (results, total)
