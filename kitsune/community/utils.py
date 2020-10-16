import hashlib
from datetime import date, datetime, timedelta
from operator import itemgetter

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

from kitsune.products.models import Product
from kitsune.users.models import User, UserMappingType
from kitsune.wiki.models import Revision

from elasticsearch_dsl import A
from kitsune.search.v2.documents import AnswerDocument, ProfileDocument


def top_contributors_questions(start=None, end=None, locale=None, product=None, count=10):
    """Get the top Support Forum contributors."""

    search = AnswerDocument.search()

    search = search.filter(
        # filter out answers by the question author
        "script",
        script="doc['creator_id'].value != doc['question_creator_id'].value",
    ).filter(
        # filter answers created between `start` and `end`, or within the last 90 days
        "range",
        created={"gte": start or datetime.now() - timedelta(days=90), "lte": end},
    )
    if locale:
        search = search.filter("term", locale=locale)
    if product:
        search = search.filter("term", question_product_id=product.id)

    search.aggs.bucket(
        # create buckets for the `count + 1` most active contributors
        "contributions",
        A("terms", field="creator_id", size=count + 1),
    ).bucket(
        # within each of those, create a bucket for the most recent answer, and extract its date
        "latest",
        A(
            "top_hits",
            sort={"created": {"order": "desc"}},
            _source={"includes": "created"},
            size=1,
        ),
    )

    contribution_buckets = search.execute().aggregations.contributions.buckets
    total_contributors = len(contribution_buckets)

    if not total_contributors:
        return [], 0

    user_ids = [bucket.key for bucket in contribution_buckets[:count]]
    users = ProfileDocument.mget(user_ids, missing="none")

    top_contributors = []
    for loop_index, bucket in enumerate(contribution_buckets[:count]):
        user = users[loop_index]
        if user is None:
            continue
        if bucket.key != user.meta.id:
            raise RuntimeError("ES returned profiles out of order")
        last_activity = datetime.fromisoformat(bucket.latest.hits.hits[0]._source.created)
        days_since_last_activity = (datetime.now() - last_activity).days
        top_contributors.append(
            {
                "count": bucket.doc_count,
                "term": bucket.key,
                "user": {
                    "id": user.meta.id,
                    "username": user.username,
                    "display_name": user.name,
                    "avatar": getattr(user.avatar, "url", None),
                    "days_since_last_activity": days_since_last_activity,
                },
            }
        )

    return top_contributors, total_contributors


def top_contributors_kb(start=None, end=None, product=None, count=10, page=1, use_cache=True):
    """Get the top KB editors (locale='en-US')."""
    return top_contributors_l10n(
        start, end, settings.WIKI_DEFAULT_LANGUAGE, product, count, use_cache
    )


def top_contributors_l10n(
    start=None, end=None, locale=None, product=None, count=10, page=1, use_cache=True
):
    """Get the top l10n contributors for the KB."""
    if use_cache:
        cache_key = "{}_{}_{}_{}_{}_{}".format(start, end, locale, product, count, page)
        cache_key = hashlib.sha1(cache_key.encode("utf-8")).hexdigest()
        cache_key = "top_contributors_l10n_{}".format(cache_key)
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


def top_contributors_aoa(start=None, end=None, locale=None, count=10, page=1, use_cache=True):
    """Get the top Army of Awesome contributors."""
    # AoA is deprecated, return 0 until we remove all related code.
    return ([], 0)


def _get_creator_counts(query, count, page):
    total = query.count()

    start = (page - 1) * count
    end = page * count
    query_data = query.values("id", "query_count")[start:end]

    query_data = {obj["id"]: obj["query_count"] for obj in query_data}

    users_data = (
        UserMappingType.search()
        .filter(id__in=list(query_data.keys()))
        .values_dict(
            "id",
            "username",
            "display_name",
            "avatar",
            "twitter_usernames",
            "last_contribution_date",
        )[:count]
    )

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
