from operator import itemgetter
from datetime import date, timedelta

from django.db.models import Count

from tastypie.resources import Resource
from tastypie import fields
from tastypie.authorization import Authorization

from questions.models import Question
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

        # Remap
        w = _remap_date_counts(qs_with_solutions, 'solved')
        wo = _remap_date_counts(qs, 'questions')

        # Merge
        return _merge_list_of_dicts('date', w, wo)

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta:
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

        # Remap
        kb_votes = _remap_date_counts(qs, 'kb_votes')
        kb_helpful = _remap_date_counts(qs_helpful_votes, 'kb_helpful')

        # Merge
        return _merge_list_of_dicts('date', kb_votes, kb_helpful)

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta:
        resource_name = 'kpi_vote'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')


def _start_date():
    """The date from which we start querying data."""
    # Lets start on the first day of the month a year ago
    year_ago = date.today() - timedelta(days=365)
    return date(year_ago.year, year_ago.month, 1)


def _remap_date_counts(qs, label):
    """Remap the query result.

    From: [{'count': 2085, 'month': 11, 'year': 2010},...]
    To: {'<label>': 2085, 'date': '2010-11-01'}
    """
    return [{'date': date(x['year'], x['month'], 1), label: x['count']}
            for x in qs]


def _merge_list_of_dicts(key, *args):
    """Merge a lists of dicts into one list, grouping them by key.

    All dicts in the lists must have the specified key.

    From:
        [{"date": "2011-10-01", "votes": 3},...]
        [{"date": "2011-10-01", "helpful": 7},...]
        ...
    To:
        [{"date": "2011-10-01", "votes": 3, "helpful": 7, ...},...]
    """
    result_dict = {}
    result_list = []

    # Build the dict
    for l in args:
        for d in l:
            val = d.pop(key)
            if val in result_dict:
                result_dict[val].update(d)
            else:
                result_dict[val] = d

    # Convert to a list
    for k in sorted(result_dict.keys(), reverse=True):
        d = result_dict[k]
        d.update({key: k})
        result_list.append(Struct(**d))

    return result_list
