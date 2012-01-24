from operator import itemgetter
from datetime import date, timedelta

from django.db.models import Count, F

from tastypie.resources import Resource
from tastypie import fields
from tastypie.authorization import Authorization

from questions.models import Question, Answer
from wiki.models import HelpfulVote


class PermissionAuthorization(Authorization):
    def __init__(self, perm):
        self.perm = perm

    def is_authorized(self, request, object=None):
        return request.user.has_perm(self.perm)


class Struct:
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
        # TODO: Cache the result.

        # Set up the query for the data we need
        qs = Question.objects.filter(created__gte=_start_date()).extra(
            select={
                'month': 'extract( month from created )',
                'year': 'extract( year from created )',
            }).values('year', 'month').annotate(count=Count('created'))

        # Filter on solution
        qs_with_solutions = qs.filter(solution__isnull=False)

        # Merge
        return merge_results(solved=qs_with_solutions, questions=qs)

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta:
        resource_name = 'kpi_solution'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')


class ArticleVoteResource(Resource):
    """
    Returns the number of total and helpful votes.
    """
    date = fields.DateField('date')
    helpful = fields.IntegerField('helpful', default=0)
    votes = fields.IntegerField('votes', default=0)

    def get_object_list(self, request):
        # TODO: Cache the result.

        # Set up the query for the data we need
        qs = HelpfulVote.objects.filter(created__gte=_start_date()).extra(
            select={
                'month': 'extract( month from created )',
                'year': 'extract( year from created )',
            }).values('year', 'month').annotate(count=Count('created'))

        # Filter on helpful
        qs_helpful_votes = qs.filter(helpful=True)

        # Merge
        return merge_results(votes=qs, helpful=qs_helpful_votes)

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta:
        resource_name = 'kpi_kbvote'
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

        # Set up the query for the data we need
        qs = Question.objects.filter(created__gte=_start_date()).extra(
            select={
                'month': 'extract( month from created )',
                'year': 'extract( year from created )',
            }).values('year', 'month').annotate(count=Count('created'))

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
