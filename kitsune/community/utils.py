import hashlib
from datetime import date, datetime, timedelta
from operator import itemgetter

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, F

from kitsune.products.models import Product
from kitsune.questions.models import Answer
from kitsune.users.models import User, UserMappingType
from kitsune.wiki.models import Revision


def top_contributors_questions(
    start=None, end=None, locale=None, product=None, count=10, page=1, use_cache=True
):
    """Get the top Support Forum contributors."""
    if use_cache:
        cache_key = '{}_{}_{}_{}_{}_{}'.format(start, end, locale, product, count, page)
        cache_key = hashlib.sha1(cache_key.encode('utf-8')).hexdigest()
        cache_key = 'top_contributors_questions_{}'.format(cache_key)
        cached = cache.get(cache_key, None)
        if cached:
            return cached

    answers = (
        Answer.objects.exclude(is_spam=True).exclude(question__is_spam=True)
        # Adding answer to your own question, isn't a contribution.
        .exclude(creator_id=F("question__creator_id"))
    )

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

    users = (
        User.objects.filter(answers__in=answers)
        .annotate(query_count=Count("answers"))
        .order_by("-query_count")
    )
    counts = _get_creator_counts(users, count, page)

    if use_cache:
        cache.set(cache_key, counts, 60 * 180)  # 3 hours
    return counts


def top_contributors_kb(
    start=None, end=None, product=None, count=10, page=1, use_cache=True
):
    """Get the top KB editors (locale='en-US')."""
    return top_contributors_l10n(
        start, end, settings.WIKI_DEFAULT_LANGUAGE, product, count, use_cache
    )


def top_contributors_l10n(
    start=None, end=None, locale=None, product=None, count=10, page=1, use_cache=True
):
    """Get the top l10n contributors for the KB."""
    if use_cache:
        cache_key = '{}_{}_{}_{}_{}_{}'.format(start, end, locale, product, count, page)
        cache_key = hashlib.sha1(cache_key.encode('utf-8')).hexdigest()
        cache_key = 'top_contributors_l10n_{}'.format(cache_key)
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

    users = (
        User.objects.filter(created_revisions__in=revisions)
        .annotate(query_count=Count("created_revisions"))
        .order_by("-query_count")
    )
    counts = _get_creator_counts(users, count, page)

    if use_cache:
        cache.set(cache_key, counts, 60 * 180)  # 3 hours
    return counts


def top_contributors_aoa(
    start=None, end=None, locale=None, count=10, page=1, use_cache=True
):
    """Get the top Army of Awesome contributors."""
    # AoA is deprecated, return 0 until we remove all related code.
    return ([], 0)


def _get_creator_counts(query, count, page):
    total = query.count()

    start = (page - 1) * count
    end = page * count
    query_data = query.values('id', 'query_count')[start:end]

    query_data = {obj['id']: obj['query_count'] for obj in query_data}

    users_data = (UserMappingType.search().filter(id__in=list(query_data.keys()))
                                 .values_dict('id', 'username', 'display_name',
                                              'avatar', 'twitter_usernames',
                                              'last_contribution_date')[:count])

    users_data = UserMappingType.reshape(users_data)

    results = []
    now = datetime.now()

    for u_data in users_data:
        user_id = u_data.get("id")
        last_contribution_date = u_data.get("last_contribution_date", None)

        u_data["days_since_last_activity"] = (
            (now - last_contribution_date).days if last_contribution_date else None
        )

        data = {"count": query_data.get(user_id), "term": user_id, "user": u_data}

        results.append(data)

    # Descending Order the list according to count.
    # As the top number of contributor should be at first
    results = sorted(results, key=itemgetter("count"), reverse=True)

    return results, total
