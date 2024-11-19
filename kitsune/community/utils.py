import hashlib
from datetime import date, datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db.models import Count, F, Q
from django.db.models.functions import Now
from elasticsearch_dsl import A

from kitsune.products.models import Product
from kitsune.search.documents import AnswerDocument, ProfileDocument
from kitsune.users.models import ContributionAreas, User
from kitsune.users.templatetags.jinja_helpers import profile_avatar
from kitsune.wiki.models import Revision


def top_contributors_questions(start=None, end=None, locale=None, product=None, count=10, page=1):
    """Get the top Support Forum contributors."""

    search = AnswerDocument.search()

    search = (
        search.filter(
            # filter out answers by the question author
            "script",
            script="doc['creator_id'].value != doc['question_creator_id'].value",
        ).filter(
            # filter answers created between `start` and `end`, or within the last 90 days
            "range",
            created={"gte": start or datetime.now() - timedelta(days=90), "lte": end},
        )
        # set the query size to 0 because we don't care about the results
        # we're just filtering for the aggregations defined below
        .extra(size=0)
    )
    if locale:
        search = search.filter("term", locale=locale)
    if product:
        search = search.filter("term", question_product_id=product.id)

    # our filters above aren't perfect, and don't only return answers from contributors
    # so we need to collect more buckets than `count`, so we can hopefully find `count`
    # number of contributors within
    search.aggs.bucket(
        # create buckets for the `count * 10` most active users
        "contributions",
        A("terms", field="creator_id", size=count * 10),
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

    if not contribution_buckets:
        return [], 0

    user_ids = [bucket.key for bucket in contribution_buckets]
    contributor_group_ids = list(
        Group.objects.filter(name__in=ContributionAreas.get_groups()).values_list("id", flat=True)
    )

    # fetch all the users returned by the aggregation which are in the contributor groups
    user_hits = (
        ProfileDocument.search()
        .query("terms", **{"_id": user_ids})
        .query("terms", group_ids=contributor_group_ids)
        .extra(size=len(user_ids))
        .execute()
        .hits
    )
    users = {hit.meta.id: hit for hit in user_hits}

    total_contributors = len(user_hits)
    top_contributors = []
    for bucket in contribution_buckets:
        if len(top_contributors) == page * count:
            # stop once we've collected enough contributors
            break
        user = users.get(bucket.key)
        if user is None:
            continue
        last_activity = datetime.fromisoformat(bucket.latest.hits.hits[0]._source.created)
        days_since_last_activity = (datetime.now(tz=timezone.utc) - last_activity).days
        top_contributors.append(
            {
                "count": bucket.doc_count,
                "term": bucket.key,
                "user": {
                    "id": user.meta.id,
                    "username": user.username,
                    "display_name": user.name,
                    "avatar": getattr(getattr(user, "avatar", None), "url", None),
                    "days_since_last_activity": days_since_last_activity,
                },
            }
        )

    return top_contributors[count * (page - 1) :], total_contributors


def top_contributors_kb(**kwargs):
    """Get the top KB editors (locale='en-US')."""
    kwargs["locale"] = settings.WIKI_DEFAULT_LANGUAGE
    return top_contributors_l10n(**kwargs)


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

    if start is None:
        # By default we go back 90 days.
        start = date.today() - timedelta(days=90)

    # Get the user ids and contribution count of the top contributors.
    revisions = Revision.objects.all()
    revisions = revisions.filter(created__range=(start, end or Now()))
    if locale:
        revisions = revisions.filter(document__locale=locale)
    else:
        # If there is no locale specified, exclude en-US only. The rest are l10n.
        revisions = revisions.exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
    if product:
        if isinstance(product, Product):
            product = product.slug
        revisions = revisions.filter(
            Q(document__products__slug=product) | Q(document__parent__products__slug=product)
        )

    users = (
        User.objects.filter(created_revisions__in=revisions, is_active=True)
        .exclude(profile__is_bot=True)
        .annotate(query_count=Count("created_revisions"))
        .order_by(F("query_count").desc(nulls_last=True))
        .select_related("profile")
    )
    total = users.count()

    results = [
        {
            "term": user.pk,
            "count": user.query_count,
            "user": {
                "id": user.pk,
                "username": user.username,
                "display_name": user.profile.display_name,
                "avatar": profile_avatar(user),
            },
        }
        for user in users[(page - 1) * count : page * count]
    ]

    if use_cache:
        cache.set(cache_key, (results, total), settings.CACHE_MEDIUM_TIMEOUT)
    return results, total
