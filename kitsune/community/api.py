from collections import defaultdict
from datetime import datetime, timedelta

from elasticutils import F
from rest_framework import views, fields
from rest_framework.response import Response

from kitsune.questions.models import AnswerMetricsMappingType
from kitsune.users.models import UserMappingType


# This should be the higher than the max number of contributors for a
# section.  There isn't a way to tell ES to just return everything.
BIG_NUMBER = 10000


class TopContributorsQuestions(views.APIView):

    def get(self, request):
        return Response(self.get_data(request))

    def get_filters(self):
        f = F(by_asker=False)

        self.filter_values = {
            'startdate': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            'enddate': datetime.now().strftime('%Y-%m-%d'),
        }
        # request.GET is a multidict, so simple `.update(request.GET)` causes
        # everything to be a list. This converts it into a plain single dict.
        self.filter_values.update(dict(self.request.GET.items()))

        for key, value in self.filter_values.items():
            filter_method = getattr(self, 'filter_' + key, lambda v: F())
            f &= filter_method(value)

        return f

    def filter_startdate(self, value):
        date = fields.DateField().from_native(value)
        dt = datetime.combine(date, datetime.min.time())
        return F(created__gte=dt)

    def filter_enddate(self, value):
        date = fields.DateField().from_native(value)
        dt = datetime.combine(date, datetime.max.time())
        return F(created__lte=dt)

    def filter_username(self, value):
        username_lower = value.lower()

        username_filter = (
            F(iusername__prefix=username_lower) |
            F(idisplay_name__prefix=username_lower) |
            F(itwitter_usernames__prefix=username_lower))

        users = UserMappingType.reshape(
            UserMappingType
            .search()
            .filter(username_filter)
            .values_dict('id')
            [:BIG_NUMBER])

        return F(creator_id__in=[u['id'] for u in users])

    def filter_locale(self, value):
        return F(locale=value)

    def get_data(self, request):
        # So filters can use the request.
        self.request = request

        # This is the base of all the metrics. Each metric branches off from
        # this to get a particular metric type, since we can't do Aggregates.
        query = AnswerMetricsMappingType.search()
        base_filter = self.get_filters()

        # This branch is to get the total number of answers for each user.
        answer_query = (
            query
            .filter(base_filter)
            .facet('creator_id', filtered=True, size=BIG_NUMBER))

        # This branch gets the number of answers that are solutions for each user.
        solutions_filter = base_filter & F(is_solution=True)
        solutions_query = (
            query
            .filter(solutions_filter)
            .facet('creator_id', filtered=True, size=BIG_NUMBER))

        # This branch gets the number of helpful votes across all answers for
        # each user. It is a raw facet because elasticutils only supports the
        # term facet type in non-raw facets. Because it is raw facet, we have
        # to also put the filter in the facet ourselves.
        helpful_query = (
            query
            .facet_raw(
                creator_id={
                    'terms_stats': {
                        'key_field': 'creator_id',
                        'value_field': 'helpful_count',
                    },
                    'facet_filter': query._process_filters(base_filter.filters),
                }))

        # Collect three lists of objects that correlates users and the appropriate metric count
        creator_answer_counts = answer_query.facet_counts()['creator_id']['terms']
        creator_solutions_counts = solutions_query.facet_counts()['creator_id']['terms']
        creator_helpful_counts = helpful_query.facet_counts()['creator_id']['terms']

        # Combine all the metric types into one big list.
        combined = defaultdict(lambda: {
            'answer_count': 0,
            'solution_count': 0,
            'helpful_vote_count': 0,
        })

        for d in creator_answer_counts:
            combined[d['term']]['user_id'] = d['term']
            combined[d['term']]['answer_count'] = d['count']

        for d in creator_solutions_counts:
            combined[d['term']]['user_id'] = d['term']
            combined[d['term']]['solution_count'] = d['count']

        for d in creator_helpful_counts:
            combined[d['term']]['user_id'] = d['term']
            # Since this is a term_stats filter, not just a term filter, it is total, not count.
            combined[d['term']]['helpful_vote_count'] = d['total']

        # Sort by answer count, and get just the ids into a list.
        top_contributors = combined.values()
        top_contributors.sort(key=lambda d: d['answer_count'], reverse=True)
        user_ids = [c['user_id'] for c in top_contributors]
        full_count = len(user_ids)

        # Paginate those user ids.
        try:
            page = int(self.request.GET.get('page', 1))
        except ValueError:
            page = 1
        count = 10
        page_start = (page - 1) * count
        page_end = page_start + count
        user_ids = user_ids[page_start:page_end]

        # Get full user objects for every id on this page.
        users = UserMappingType.reshape(
            UserMappingType
            .search()
            .filter(id__in=user_ids)
            .values_dict('id', 'username', 'display_name', 'avatar', 'last_contribution_date')
            [:count])

        # For ever user object found, mix in the metrics counts for that user,
        # and then reshape the data to make more sense to clients.
        data = []
        for u in users:
            d = combined[u['id']]
            d['user'] = u
            d['last_contribution_date'] = d['user'].get('last_contribution_date', None)
            if 'user_id' in d:
                del d['user_id']
            del d['user']['id']
            if 'last_contribution_date' in d['user']:
                del d['user']['last_contribution_date']
            data.append(d)

        # One last sort, since ES didn't return the users in any particular order.
        data.sort(key=lambda d: d['answer_count'], reverse=True)

        # Add ranks to the objects.
        for i, contributor in enumerate(data, 1):
            contributor['rank'] = page_start + i

        return {
            'results': data,
            'count': full_count,
            'filters': self.filter_values,
        }
