from operator import itemgetter, attrgetter
from datetime import date

from django.db.models import Count

from tastypie.resources import Resource
from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization

from questions.models import Question


class PermissionAuthorization(Authorization):
    def __init__(self, perm):
        self.perm = perm

    def is_authorized(self, request, object=None):
        return request.user.has_perm(self.perm)


class Struct:
    """Convert a dict to an object"""
    def __init__(self, **entries):
        self.__dict__.update(entries)


class SolutionResource(Resource):
    """
    Returns the number of questions with
    and without an answer maked as the solution.
    """
    date = fields.DateField('date')
    with_solutions = fields.IntegerField('solutions', default=0)
    without_solutions = fields.IntegerField('without_solutions', default=0)

    def get_object_list(self, request):
        # Set up the query for the data we need
        qs = Question.objects.extra(
            select={
                'month': 'extract( month from created )',
                'year': 'extract( year from created )',
            }).values('year', 'month').annotate(count=Count('created'))

        # Filter on solution
        qs_without_solutions = qs.exclude(solution__isnull=False)
        qs_with_solutions = qs.filter(solution__isnull=False)

        # Wonky re mapping to go from
        # [{'date': '8-2011', 'solutions': 707},
        # {'date': '7-2011', 'solutions': 740},...]
        # to
        # {'1-2010': {'solutions': 1},
        # '1-2011': {'solutions': 294},...}
        w = dict((date(x['year'], x['month'], 1),
                  {'solutions': x['count']}) for x in qs_with_solutions)
        wo = dict((date(x['year'], x['month'], 1),
                   {'without_solutions': x['count']})
                  for x in qs_without_solutions)

        # merge the reuslts
        # [{ "date": "2011-10-01",
        #    "resource_uri": "",
        #    "with_solutions": 1,
        #    "without_solutions": 5
        #  }, {
        #    "date": "2011-08-01",
        #    "resource_uri": "",
        #    "with_solutions": 707,
        #    "without_solutions": 8144
        #  }, ...]
        res_dict = dict((s, dict(w.get(s, {}).items() + wo.get(s, {}).items()))
                        for s in set(w.keys() + wo.keys()))
        res_list = [dict(date=k, **v) for k, v in res_dict.items()]
        return [Struct(**x) for x in sorted(res_list, key=itemgetter('date'),
                                            reverse=True)]

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    class Meta:
        resource_name = 'kpi_solution'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')
