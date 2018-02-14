import hashlib

from datetime import datetime, date, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, F

from kitsune.products.models import Product
from kitsune.questions.models import Answer
from kitsune.users.models import User
from kitsune.users.templatetags.jinja_helpers import profile_avatar
from kitsune.wiki.models import Revision


def top_contributors_questions(start=None, end=None, locale=None, product=None,
                               count=10, page=1, use_cache=True):
    """Get the top Support Forum contributors."""
    if use_cache:
        cache_key = u'{}_{}_{}_{}_{}_{}'.format(start, end, locale, product, count, page)
        cache_key = hashlib.sha1(cache_key.encode('utf-8')).hexdigest()
        cache_key = 'top_contributors_questions_{}'.format(cache_key)
        cached = cache.get(cache_key, None)
        if cached:
            return cached

    answers = (Answer.objects
               .exclude(is_spam=True)
               .exclude(question__is_spam=True)
               # Adding answer to your own question, isn't a contribution.
               .exclude(creator_id=F('question__creator_id')))

    if start is None:
        # By default we go back 90 days.
        start = date.today() - timedelta(days=90)
        answers = answers.filter(created__gte=start)
    if end:
        # If no end is specified, we don't need to filter by it.
        answers = answers.filter(created__lt=end)
    if locale:
        answers = answers.filter(question__locale=locale)
    if product:
        if isinstance(product, Product):
            product = product.slug
        answers = answers.filter(question__product__slug=product)

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
        cache_key = u'{}_{}_{}_{}_{}_{}'.format(start, end, locale, product, count, page)
        cache_key = hashlib.sha1(cache_key.encode('utf-8')).hexdigest()
        cache_key = u'top_contributors_l10n_{}'.format(cache_key)
        cached = cache.get(cache_key, None)
        if cached:
            return cached

    # Get the user ids and contribution count of the top contributors.
    revisions = Revision.objects.all()
    if locale is None:
        # If there is no locale specified, exclude en-US only. The rest are
        # l10n.
        revisions = revisions.exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
    if start is None:
        # By default we go back 90 days.
        start = date.today() - timedelta(days=90)
        revisions = revisions.filter(created__gte=start)
    if end:
        # If no end is specified, we don't need to filter by it.
        revisions = revisions.filter(created__lt=end)
    if locale:
        revisions = revisions.filter(document__locale=locale)
    if product:
        if isinstance(product, Product):
            product = product.slug
        revisions = revisions.filter(document__products__slug=product)

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
    # AoA is deprecated, return 0 until we remove all related code.
    return ([], 0)


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
