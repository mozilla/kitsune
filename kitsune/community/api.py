from collections import defaultdict
from datetime import datetime, timedelta

from elasticutils import F
from rest_framework import views, fields, exceptions
from rest_framework.response import Response

from kitsune.questions.models import AnswerMetricsMappingType
from kitsune.users.models import UserMappingType
from kitsune.wiki.models import RevisionMetricsMappingType


# This should be the higher than the max number of contributors for a
# section.  There isn't a way to tell ES to just return everything.
BIG_NUMBER = 10000


class InvalidFilterNameException(exceptions.APIException):
    """A filter was requested which does not exist."""

    def __init__(self, detail, **kwargs):
        self.status_code = 400
        self.detail = detail
        for key, val in list(kwargs.items()):
            setattr(self, key, val)


class TopContributorsBase(views.APIView):
    def __init__(self):
        super(TopContributorsBase, self)
        self.warnings = []

    def get(self, request):
        return Response(self.get_data(request))

    def get_data(self, request):
        # So filters can use the request.
        self.request = request
        return {}

    def get_allowed_orderings(self):
        return []

    def get_filters(self):
        self.query_values = self.get_default_query()
        # request.GET is a multidict, so simple `.update(request.GET)` causes
        # everything to be a list. This converts it into a plain single dict.
        self.query_values.update(dict(list(self.request.GET.items())))

        f = F()

        for key, value in list(self.query_values.items()):
            filter_method = getattr(self, "filter_" + key, None)
            if filter_method is None:
                self.warnings.append("Unknown filter {}".format(key))
            else:
                f &= filter_method(value)

        return f

    def get_default_query(self):
        return {
            "page": 1,
            "page_size": 20,
            "startdate": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
            "enddate": datetime.now().strftime("%Y-%m-%d"),
        }

    def filter_page(self, value):
        """Validate the page numbers, but don't return any filters."""
        try:
            page = fields.IntegerField().to_internal_value(value)
        except fields.ValidationError:
            page = 1

        if page < 1:
            page = 1

        self.query_values["page"] = page

        return F()

    def filter_page_size(self, value):
        """Validate the page sizes, but don't return any filters."""
        try:
            page_size = fields.IntegerField().to_internal_value(value)
        except fields.ValidationError:
            page_size = 20

        if not (1 <= page_size < 100):
            page_size = 100

        self.query_values["page_size"] = page_size

        return F()

    def filter_ordering(self, value):
        """Validate sort order, but don't return any filters."""
        if value not in self.get_allowed_orderings():
            self.warnings.append("Invalid sort order: {}".format(value))

        return F()

    def filter_startdate(self, value):
        date = fields.DateField().to_internal_value(value)
        dt = datetime.combine(date, datetime.min.time())
        return F(created__gte=dt)

    def filter_enddate(self, value):
        date = fields.DateField().to_internal_value(value)
        dt = datetime.combine(date, datetime.max.time())
        return F(created__lte=dt)

    def filter_locale(self, value):
        return F(locale=value)

    def _filter_by_users(self, users_filter, invert=False):
        users = UserMappingType.reshape(
            UserMappingType.search()
            # Optimization: Filter out users that have never contributed.
            .filter(~F(last_contribution_date=None))
            .filter(users_filter)
            .values_dict("id")
            .everything()
        )

        user_ids = [u["id"] for u in users]

        res = F(creator_id__in=user_ids)
        if invert:
            res = ~res
        return res

    def filter_username(self, value):
        username_lower = value.lower()

        username_filter = (
            F(iusername__prefix=username_lower)
            | F(idisplay_name__prefix=username_lower)
            | F(itwitter_usernames__prefix=username_lower)
        )

        return self._filter_by_users(username_filter)

    def filter_last_contribution_date__gt(self, value):
        date = fields.DateField().to_internal_value(value)
        dt = datetime.combine(date, datetime.max.time())
        return self._filter_by_users(F(last_contribution_date__gt=dt))

    def filter_last_contribution_date__lt(self, value):
        # This query usually covers a lot of users, so inverting it makes it a lot faster.
        date = fields.DateField().to_internal_value(value)
        dt = datetime.combine(date, datetime.max.time())
        return self._filter_by_users(~F(last_contribution_date__lt=dt), invert=True)

    def filter_product(self, value):
        return F(product=value)


class TopContributorsQuestions(TopContributorsBase):
    def get_default_query(self):
        filters = super(TopContributorsQuestions, self).get_default_query()
        filters["ordering"] = "-answer_count"
        return filters

    def get_allowed_orderings(self):
        return [
            "answer_count",
            "solution_count",
            "helpful_vote_count",
        ]

    def get_filters(self):
        f = super(TopContributorsQuestions, self).get_filters()
        f &= F(by_asker=False)
        return f

    def get_data(self, request):
        super(TopContributorsQuestions, self).get_data(request)

        # This is the base of all the metrics. Each metric branches off from
        # this to get a particular metric type, since we can't do Aggregates.
        query = AnswerMetricsMappingType.search()
        base_filters = self.get_filters()

        # This branch is to get the total number of answers for each user.
        answer_query = query.filter(base_filters).facet(
            "creator_id", filtered=True, size=BIG_NUMBER
        )

        # This branch gets the number of answers that are solutions for each user.
        solutions_filter = base_filters & F(is_solution=True)
        solutions_query = query.filter(solutions_filter).facet(
            "creator_id", filtered=True, size=BIG_NUMBER
        )

        # This branch gets the number of helpful votes across all answers for
        # each user. It is a raw facet because elasticutils only supports the
        # term facet type in non-raw facets. Because it is raw facet, we have
        # to also put the filter in the facet ourselves.
        helpful_query = query.facet_raw(
            creator_id={
                "terms_stats": {"key_field": "creator_id", "value_field": "helpful_count",},
                "facet_filter": query._process_filters(base_filters.filters),
            }
        )

        # Collect three lists of objects that correlates users and the appropriate metric count
        creator_answer_counts = answer_query.facet_counts()["creator_id"]["terms"]
        creator_solutions_counts = solutions_query.facet_counts()["creator_id"]["terms"]
        creator_helpful_counts = helpful_query.facet_counts()["creator_id"]["terms"]

        # Combine all the metric types into one big list.
        combined = defaultdict(
            lambda: {"answer_count": 0, "solution_count": 0, "helpful_vote_count": 0,}
        )

        for d in creator_answer_counts:
            combined[d["term"]]["user_id"] = d["term"]
            combined[d["term"]]["answer_count"] = d["count"]

        for d in creator_solutions_counts:
            combined[d["term"]]["user_id"] = d["term"]
            combined[d["term"]]["solution_count"] = d["count"]

        for d in creator_helpful_counts:
            combined[d["term"]]["user_id"] = d["term"]
            # Since this is a term_stats filter, not just a term filter, it is total, not count.
            combined[d["term"]]["helpful_vote_count"] = int(d["total"])

        # Sort by answer count, and get just the ids into a list.
        sort_key = self.query_values["ordering"]
        if sort_key[0] == "-":
            sort_reverse = True
            sort_key = sort_key[1:]
        else:
            sort_reverse = False

        top_contributors = list(combined.values())
        top_contributors.sort(key=lambda d: d[sort_key], reverse=sort_reverse)
        user_ids = [c["user_id"] for c in top_contributors]
        full_count = len(user_ids)

        # Paginate those user ids.
        page_start = (self.query_values["page"] - 1) * self.query_values["page_size"]
        page_end = page_start + self.query_values["page_size"]
        user_ids = user_ids[page_start:page_end]

        # Get full user objects for every id on this page.
        users = UserMappingType.reshape(
            UserMappingType.search()
            .filter(id__in=user_ids)
            .values_dict("id", "username", "display_name", "avatar", "last_contribution_date")[
                : self.query_values["page_size"]
            ]
        )

        # For ever user object found, mix in the metrics counts for that user,
        # and then reshape the data to make more sense to clients.
        data = []
        for u in users:
            d = combined[u["id"]]
            d["user"] = u
            d["last_contribution_date"] = d["user"].get("last_contribution_date", None)
            d.pop("user_id", None)
            d["user"].pop("id", None)
            d["user"].pop("last_contribution_date", None)
            data.append(d)

        # One last sort, since ES didn't return the users in any particular order.
        data.sort(key=lambda d: d[sort_key], reverse=sort_reverse)

        # Add ranks to the objects.
        for i, contributor in enumerate(data, 1):
            contributor["rank"] = page_start + i

        return {
            "results": data,
            "count": full_count,
            "filters": self.query_values,
            "allowed_orderings": self.get_allowed_orderings(),
            "warnings": self.warnings,
        }


class TopContributorsLocalization(TopContributorsBase):
    def get_default_query(self):
        filters = super(TopContributorsLocalization, self).get_default_query()
        filters["ordering"] = "-revision_count"
        return filters

    def get_allowed_orderings(self):
        return [
            "revision_count",
            "review_count",
        ]

    def get_data(self, request):
        super(TopContributorsLocalization, self).get_data(request)

        # This is the base of all the metrics. Each metric branches off from
        # this to get a particular metric type, since we can't do Aggregates.
        base_query = RevisionMetricsMappingType.search()
        base_filters = self.get_filters()

        # This branch is to get the number of revisions made by each user.
        revision_query = base_query.filter(base_filters).facet(
            "creator_id", filtered=True, size=BIG_NUMBER
        )

        # This branch is to get the number of reviews done by each user.
        reviewer_query = base_query.filter(base_filters).facet(
            "reviewer_id", filtered=True, size=BIG_NUMBER
        )

        # Collect two lists of objects that correlates users and the appropriate metric count
        revision_creator_counts = revision_query.facet_counts()["creator_id"]["terms"]
        revision_reviewer_counts = reviewer_query.facet_counts()["reviewer_id"]["terms"]

        # Combine all the metric types into one big list.
        combined = defaultdict(lambda: {"revision_count": 0, "review_count": 0,})

        for d in revision_creator_counts:
            combined[d["term"]]["user_id"] = d["term"]
            combined[d["term"]]["revision_count"] = d["count"]

        for d in revision_reviewer_counts:
            combined[d["term"]]["user_id"] = d["term"]
            combined[d["term"]]["review_count"] = d["count"]

        # Sort by revision count, and get just the ids into a list.
        sort_key = self.query_values["ordering"]
        if sort_key[0] == "-":
            sort_reverse = True
            sort_key = sort_key[1:]
        else:
            sort_reverse = False

        top_contributors = list(combined.values())
        top_contributors.sort(key=lambda d: d[sort_key], reverse=sort_reverse)
        user_ids = [c["user_id"] for c in top_contributors]
        full_count = len(user_ids)

        # Paginate those user ids.
        page_start = (self.query_values["page"] - 1) * self.query_values["page_size"]
        page_end = page_start + self.query_values["page_size"]
        user_ids = user_ids[page_start:page_end]

        # Get full user objects for every id on this page.
        users = UserMappingType.reshape(
            UserMappingType.search()
            .filter(id__in=user_ids)
            .values_dict("id", "username", "display_name", "avatar", "last_contribution_date")[
                : self.query_values["page_size"]
            ]
        )

        # For ever user object found, mix in the metrics counts for that user,
        # and then reshape the data to make more sense to clients.
        data = []
        for u in users:
            d = combined[u["id"]]
            d["user"] = u
            d["last_contribution_date"] = d["user"].get("last_contribution_date", None)
            d.pop("user_id", None)
            d["user"].pop("id", None)
            d["user"].pop("last_contribution_date", None)
            data.append(d)

        # One last sort, since ES didn't return the users in any particular order.
        data.sort(key=lambda d: d[sort_key], reverse=sort_reverse)

        # Add ranks to the objects.
        for i, contributor in enumerate(data, 1):
            contributor["rank"] = page_start + i

        return {
            "results": data,
            "count": full_count,
            "filters": self.query_values,
            "allowed_orderings": self.get_allowed_orderings(),
            "warnings": self.warnings,
        }
