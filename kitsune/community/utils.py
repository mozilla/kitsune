import hashlib
from datetime import UTC, date, datetime, time, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Count, Exists, F, Max, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, Now
from django.utils import timezone
from elasticsearch.dsl import A

from kitsune.community.models import DeletedContribution
from kitsune.products.models import Product
from kitsune.questions.models import Answer
from kitsune.search.documents import AnswerDocument, ProfileDocument
from kitsune.users.models import ContributionAreas, User
from kitsune.users.templatetags.jinja_helpers import profile_avatar
from kitsune.wiki.models import Revision

DEFAULT_PERIOD_DAYS = 90


def top_contributors_questions(start=None, end=None, locale=None, product=None, count=10, page=1):
    """Get the top Support Forum contributors."""

    if not start:
        start = timezone.now() - timedelta(days=DEFAULT_PERIOD_DAYS)

    limit = min(count * 10, 1000)

    search = AnswerDocument.search()

    search = (
        search.filter(
            # filter out answers by the question author
            "script",
            script="doc['creator_id'].value != doc['question_creator_id'].value",
        )
        .filter(
            # filter answers created between `start` and `end`, or within the last 90 days
            "range",
            created={"gte": start, "lte": end},
        )
        # set the query size to 0 because we don't care about the results
        # we're just filtering for the aggregations defined below
        .extra(size=0)
    )
    if locale:
        search = search.filter("term", locale=locale)
    if product:
        search = search.filter("term", question_product_id=product.id)

    # The filters above don't restrict the results to contributors, so we need to
    # collect more buckets than `count`, so we can hopefully find `count` number
    # of contributors within the results.
    search.aggs.bucket(
        # create buckets for the `limit` most active users
        "contributions",
        A("terms", field="creator_id", size=limit),
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

    deletion_metrics_by_contributor = deleted_contribution_metrics_by_contributor(
        Answer,
        start=start,
        end=end,
        locale=locale,
        products=[product] if product else None,
        max_results=limit,
        limit_to_contributor_groups=True,
    )

    if not (contribution_buckets or deletion_metrics_by_contributor):
        return [], 0

    user_ids = list(
        {bucket.key for bucket in contribution_buckets}
        | {str(contributor_id) for contributor_id in deletion_metrics_by_contributor.keys()}
    )
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

    # Combine the results from ES and the results from the deleted-contributions query.
    combined_map = {}
    for bucket in contribution_buckets:
        if user := users.get(bucket.key):
            last_activity = datetime.fromisoformat(bucket.latest.hits.hits[0]._source.created)
            days_since_last_activity = (datetime.now(tz=UTC) - last_activity).days
            combined_map[bucket.key] = {
                "user": user,
                "count": bucket.doc_count,
                "days_since_last_activity": days_since_last_activity,
            }

    for contributor_id, (
        num_contributions,
        last_contribution_timestamp,
    ) in deletion_metrics_by_contributor.items():
        user_id = str(contributor_id)
        if user := users.get(user_id):
            days_since_last_activity = (timezone.now() - last_contribution_timestamp).days
            if user_info := combined_map.get(user_id):
                user_info["count"] += num_contributions
                user_info["days_since_last_activity"] = min(
                    user_info["days_since_last_activity"], days_since_last_activity
                )
            else:
                combined_map[user_id] = {
                    "user": user,
                    "count": num_contributions,
                    "days_since_last_activity": days_since_last_activity,
                }

    top_contributors = []
    # Sort by count descending, and secondarily by user id to ensure predictable ordering
    # when paging.
    for user_info in sorted(
        combined_map.values(),
        key=lambda user_info: (-user_info["count"], int(user_info["user"].meta.id)),
    )[count * (page - 1) :]:
        if len(top_contributors) == count:
            # Stop once we've collected enough contributors.
            break

        user = user_info["user"]
        top_contributors.append(
            {
                "count": user_info["count"],
                "term": user.meta.id,
                "user": {
                    "id": user.meta.id,
                    "username": user.username,
                    "display_name": getattr(user, "name", None),
                    "avatar": getattr(getattr(user, "avatar", None), "url", None),
                    "days_since_last_activity": user_info["days_since_last_activity"],
                },
            }
        )

    return top_contributors, total_contributors


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
        start = datetime.now() - timedelta(days=DEFAULT_PERIOD_DAYS)
    elif type(start) is date:
        start = datetime.combine(start, time.min)

    if end is None:
        end = Now()
    elif type(end) is date:
        end = datetime.combine(end, time.max)

    revision_ct = ContentType.objects.get_for_model(Revision)

    rev_subquery = Revision.objects.filter(creator=OuterRef("pk"), created__range=(start, end))

    del_subquery = DeletedContribution.objects.filter(
        content_type=revision_ct,
        contributor=OuterRef("pk"),
        contribution_timestamp__range=(start, end),
    )

    if locale:
        rev_subquery = rev_subquery.filter(document__locale=locale)
        del_subquery = del_subquery.filter(locale=locale)
    else:
        # If there is no locale specified, exclude en-US only. The rest are l10n.
        rev_subquery = rev_subquery.exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
        del_subquery = del_subquery.exclude(locale=settings.WIKI_DEFAULT_LANGUAGE)

    if product:
        slug = product.slug if isinstance(product, Product) else product
        rev_subquery = rev_subquery.filter(
            Q(document__products__slug=slug) | Q(document__parent__products__slug=slug)
        )
        del_subquery = del_subquery.filter(products__slug=slug)

    users = (
        User.objects.filter(is_active=True)
        .filter(Exists(rev_subquery) | Exists(del_subquery))
        .annotate(
            rev_count=Coalesce(
                Subquery(
                    rev_subquery.values("creator").annotate(count=Count("pk")).values("count")[:1]
                ),
                0,
            ),
            del_count=Coalesce(
                Subquery(
                    del_subquery.values("contributor")
                    .annotate(count=Count("pk"))
                    .values("count")[:1]
                ),
                0,
            ),
        )
        .annotate(contribution_count=F("rev_count") + F("del_count"))
        .order_by("-contribution_count", "id")
        .select_related("profile")
        .only("id", "username", "profile__name", "profile__fxa_avatar")
    )

    total = users.count()
    offset = (page - 1) * count
    paginated_users = users[offset : offset + count]

    results = [
        {
            "term": user.pk,
            "count": user.contribution_count,
            "user": {
                "id": user.pk,
                "username": user.username,
                "display_name": user.profile.display_name,
                "avatar": profile_avatar(user),
            },
        }
        for user in paginated_users
    ]

    if use_cache:
        cache.set(cache_key, (results, total), settings.CACHE_MEDIUM_TIMEOUT)
    return results, total


def num_deleted_contributions(model, exclude_locale=None, **filters):
    """
    Returns the number of deleted model instances scoped by the filters.
    """
    qs = DeletedContribution.objects.filter(
        content_type=ContentType.objects.get_for_model(model), **filters
    )
    if exclude_locale:
        qs = qs.exclude(locale=exclude_locale)

    if any(key in filters for key in ("products__in", "contributor__groups__in")):
        qs = qs.distinct()

    return qs.count()


def deleted_contribution_metrics_by_contributor(
    model,
    start=None,
    end=None,
    locale=None,
    products=None,
    max_results=None,
    limit_to_contributor_groups=False,
    **extra_filters,
):
    use_distinct = False

    filter_kwargs = {"content_type": ContentType.objects.get_for_model(model)}

    if start:
        filter_kwargs.update(contribution_timestamp__gte=start)

    if end:
        filter_kwargs.update(contribution_timestamp__lte=end)

    if locale:
        filter_kwargs.update(locale=locale)

    if products:
        use_distinct = True
        filter_kwargs.update(products__in=products)

    if limit_to_contributor_groups:
        use_distinct = True
        filter_kwargs.update(
            contributor__groups__in=Group.objects.filter(
                name__in=ContributionAreas.get_groups(),
            ),
        )

    filter_kwargs.update(extra_filters)

    qs = DeletedContribution.objects.filter(**filter_kwargs)

    if use_distinct:
        qs = qs.distinct()

    results = (
        qs.values("contributor")
        .annotate(
            total_deleted_contributions=Count("*"),
            last_contribution_timestamp=Max("contribution_timestamp"),
        )
        .order_by("-total_deleted_contributions", "contributor")
    )

    if max_results:
        results = results[:max_results]

    return {
        row["contributor"]: (
            row["total_deleted_contributions"],
            row["last_contribution_timestamp"],
        )
        for row in results
    }
