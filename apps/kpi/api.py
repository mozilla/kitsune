from operator import itemgetter
from datetime import date, timedelta

from django.db.models import Count, F
from django.core.cache import cache
from django.db.models import Count

from tastypie.resources import Resource
from tastypie import fields
from tastypie.authorization import Authorization

from questions.models import Question, Answer, AnswerVote
from wiki.models import HelpfulVote


class PermissionAuthorization(Authorization):
    def __init__(self, perm):
        self.perm = perm

    def is_authorized(self, request, object=None):
        return request.user.has_perm(self.perm)


class Struct(object):
    """Convert a dict to an object"""
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __unicode__(self):
        return unicode(self.__dict__)


class SolutionResource(Resource):
    """
    Returns the number of questions with
    and without an answer maked as the solution.
    """
    date = fields.DateField('date')
    solved = fields.IntegerField('solved', default=0)
    questions = fields.IntegerField('questions', default=0)

    def get_object_list(self, request):
        cache_key = 'kpi:solution'
        result = cache.get(cache_key)
        if result is None:
            # Set up the query for the data we need
            qs = _qs_for(Question)

            # Filter on solution
            qs_with_solutions = qs.filter(solution__isnull=False)

            result = merge_results(solved=qs_with_solutions, questions=qs)

            # Cache
            cache.add(cache_key, result)

        return result

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta(object):
        resource_name = 'kpi_solution'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')


class VoteResource(Resource):
    """
    Returns the number of total and helpful votes for Articles and Answers.
    """
    date = fields.DateField('date')
    kb_helpful = fields.IntegerField('kb_helpful', default=0)
    kb_votes = fields.IntegerField('kb_votes', default=0)
    ans_helpful = fields.IntegerField('ans_helpful', default=0)
    ans_votes = fields.IntegerField('ans_votes', default=0)

    def get_object_list(self, request):
        cache_key = 'kpi:vote'
        result = cache.get(cache_key)
        if result is None:
            # Set up the queries for the data we need
            qs_kb_votes = _qs_for(HelpfulVote)
            qs_ans_votes = _qs_for(AnswerVote)

            # Filter on helpful
            qs_kb_helpful_votes = qs_kb_votes.filter(helpful=True)
            qs_ans_helpful_votes = qs_ans_votes.filter(helpful=True)

            result = merge_results(
                        kb_votes=qs_kb_votes,
                        kb_helpful=qs_kb_helpful_votes,
                        ans_votes=qs_ans_votes,
                        ans_helpful=qs_ans_helpful_votes)
            # Cache
            cache.add(cache_key, result)

        return result

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta(object):
        resource_name = 'kpi_vote'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')


class FastResponseResource(Resource):
    """
    Returns the total number and number of Questions that recieve an answer
    within a period of time.
    """
    date = fields.DateField('date')
    questions = fields.IntegerField('questions', default=0)
    responded = fields.IntegerField('responded', default=0)

    def get_object_list(self, request):
        # TODO: Cache the result.

        qs = _qs_for(Question)

        # All answers tht were created within 3 days of the question
        aq = Answer.objects.filter(
                created__lt=F('question__created') + timedelta(days=3))
        # Qustions of said answers. This way results in a single query
        rs = qs.filter(id__in=aq.values_list('question'))

        # Merge and return
        return merge_results(responded=rs, questions=qs)

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta:
        resource_name = 'kpi_fast_response'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')

def _qs_for(model_cls):
    """Return the grouped queryset we need for model_cls."""
    return model_cls.objects.filter(created__gte=_start_date()).extra(
        select={
            'month': 'extract( month from created )',
            'year': 'extract( year from created )',
        }).values('year', 'month').annotate(count=Count('created'))


def _start_date():
    """The date from which we start querying data."""
    # Lets start on the first day of the month a year ago
    year_ago = date.today() - timedelta(days=365)
    return date(year_ago.year, year_ago.month, 1)


def _remap_date_counts(**kwargs):
    """Remap the query result.

    From: [{'count': 2085, 'month': 11, 'year': 2010},...]
    To: {'<label>': 2085, 'date': '2010-11-01'}
    """
    for label, qs in kwargs.iteritems():
        yield dict((date(x['year'], x['month'], 1), {label: x['count']})
                    for x in qs)


def merge_results(**kwargs):
    res_dict = reduce(_merge_results, _remap_date_counts(**kwargs))
    res_list = [dict(date=k, **v) for k, v in res_dict.items()]
    return [Struct(**x)
            for x in sorted(res_list, key=itemgetter('date'), reverse=True)]


def _merge_results(x, y):
    """Merge query results arrays into one array.

    From:
        [{"date": "2011-10-01", "votes": 3},...]
        and
        [{"date": "2011-10-01", "helpful": 7},...]
    To:
        [{"date": "2011-10-01", "votes": 3, "helpful": 7},...]
    """
    return dict((s, dict(x.get(s, {}).items() + y.get(s, {}).items()))
                    for s in set(x.keys() + y.keys()))
