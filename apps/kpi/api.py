from operator import itemgetter
from datetime import date, timedelta

from django.db import connections, router
from django.db.models import Count, F

from tastypie.resources import Resource
from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.cache import SimpleCache

from kpi.models import Metric, MetricKind
from questions.models import Question, Answer, AnswerVote
from wiki.models import HelpfulVote


class CachedResource(Resource):
    def obj_get_list(self, request=None, **kwargs):
        """Override ``obj_get_list`` to use the cache."""
        cache_key = self.generate_cache_key('list', **kwargs)
        obj_list = self._meta.cache.get(cache_key)

        if obj_list is None:
            obj_list = self.get_object_list(request)
            self._meta.cache.set(cache_key, obj_list, timeout=60 * 60 * 3)

        return obj_list


class PermissionAuthorization(Authorization):
    """Authorization which allows users with one permission to make read-only
    requests and users with another to write."""

    def __init__(self, read=None, write=None):
        self.read_perm = read
        self.write_perm = write

    def is_authorized(self, request, object=None):
        if request.method == 'GET':
            return request.user.has_perm(self.read_perm)
        elif request.method == 'POST':
            return request.user.has_perm(self.write_perm)
        return False


class Struct(object):
    """Convert a dict to an object"""
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __unicode__(self):
        return unicode(self.__dict__)


class SphinxClickthroughResource(Resource):  # TODO: Make cached.
    """Clickthrough ratio for Sphinx or Elastic searches for one period

    Represents a ratio of {clicks of results}/{total searches} for one engine.

    """
    #: Date of period start. Assumes 1-week periods.
    start = fields.DateField('start')
    #: How many searches had (at least?) 1 result clicked
    clicks = fields.IntegerField('clicks', default=0)
    #: How many searches were performed with this engine
    searches = fields.IntegerField('searches', default=0)

    class Meta(object):
        resource_name = 'sphinx-clickthrough-rate'
        object_class = Struct
        authorization = PermissionAuthorization(
            read='users.view_kpi_dashboard',
            write='users.change_metric')

    def obj_get(self, request=None, **kwargs):
        """Fetch a particular ratio by start date."""
        raise NotImplementedError

    def get_object_list(self, request):
        """Return the authZ-limited set of ratios"""
        # TODO: Limit by a passed-in start date.
        return self.obj_get_list(request)

    def obj_get_list(self, request=None, **kwargs):
        """Return all the ratios.

        If, somehow, half a ratio is missing, that ratio is not returned.

        """
        # I'm not sure if you can join a table to itself with the ORM.
        cursor = _cursor()
        cursor.execute(  # n for numerator, d for denominator
            'SELECT n.start, n.value, d.value '
            'FROM kpi_metric n '
            'INNER JOIN kpi_metric d ON n.start=d.start '
            'WHERE n.kind_id=(SELECT id FROM kpi_metrickind WHERE code=%s) '
            'AND d.kind_id=(SELECT id FROM kpi_metrickind WHERE code=%s)',
            ('search clickthroughs:sphinx:clicks',
             'search clickthroughs:sphinx:searches'))
        return [Struct(start=s, clicks=n, searches=d) for
                s, n, d in cursor.fetchall()]

    def obj_create(self, bundle, request=None, **kwargs):
        def create_metric(kind, value_field, data):
            """Given POSTed data, create a Metric.

            Assume week-long buckets for the moment.

            """
            start = date(*(int(i) for i in data['start'].split('-')))
            Metric.objects.create(kind=MetricKind.objects.get(code=kind),
                                  start=start,
                                  end=start + timedelta(days=7),
                                  value=data[value_field])

        create_metric('search clickthroughs:sphinx:searches',
                      'searches',
                      bundle.data)
        create_metric('search clickthroughs:sphinx:clicks',
                      'clicks',
                      bundle.data)

    def get_resource_uri(self, bundle_or_obj):
        """Return a fake answer; we don't care, for now."""
        return ''



class SolutionResource(CachedResource):
    """
    Returns the number of questions with
    and without an answer maked as the solution.
    """
    date = fields.DateField('date')
    solved = fields.IntegerField('solved', default=0)
    questions = fields.IntegerField('questions', default=0)

    def get_object_list(self, request):
        # Set up the query for the data we need
        qs = _qs_for(Question)

        # Filter on solution
        qs_with_solutions = qs.filter(solution__isnull=False)

        return merge_results(solved=qs_with_solutions, questions=qs)

    class Meta(object):
        cache = SimpleCache()
        resource_name = 'kpi_solution'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')


class VoteResource(CachedResource):
    """
    Returns the number of total and helpful votes for Articles and Answers.
    """
    date = fields.DateField('date')
    kb_helpful = fields.IntegerField('kb_helpful', default=0)
    kb_votes = fields.IntegerField('kb_votes', default=0)
    ans_helpful = fields.IntegerField('ans_helpful', default=0)
    ans_votes = fields.IntegerField('ans_votes', default=0)

    def get_object_list(self, request):
        # Set up the queries for the data we need
        qs_kb_votes = _qs_for(HelpfulVote)
        qs_ans_votes = _qs_for(AnswerVote)

        # Filter on helpful
        qs_kb_helpful_votes = qs_kb_votes.filter(helpful=True)
        qs_ans_helpful_votes = qs_ans_votes.filter(helpful=True)

        return merge_results(
                    kb_votes=qs_kb_votes,
                    kb_helpful=qs_kb_helpful_votes,
                    ans_votes=qs_ans_votes,
                    ans_helpful=qs_ans_helpful_votes)

    class Meta(object):
        cache = SimpleCache()
        resource_name = 'kpi_vote'
        allowed_methods = ['get']
        authorization = PermissionAuthorization('users.view_kpi_dashboard')


class FastResponseResource(CachedResource):
    """
    Returns the total number and number of Questions that recieve an answer
    within a period of time.
    """
    date = fields.DateField('date')
    questions = fields.IntegerField('questions', default=0)
    responded = fields.IntegerField('responded', default=0)

    def get_object_list(self, request):
        qs = _qs_for(Question)

        # All answers tht were created within 3 days of the question
        aq = Answer.objects.filter(
                created__lt=F('question__created') + timedelta(days=3))
        # Qustions of said answers. This way results in a single query
        rs = qs.filter(id__in=aq.values_list('question'))

        # Merge and return
        return merge_results(responded=rs, questions=qs)

    class Meta:
        cache = SimpleCache()
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
    kwargs = {<label>=[{'count': 45, 'month': 2L, 'year': 2010L},
     {'count': 12, 'month': 1L, 'year': 2010L},
      {'count': 1, 'month': 12L, 'year': 2009L},..],
      <label>=[{...},...],
      ...}
    returns
        [{
            datetime.date(2009, 12, 1): {'<label>': 1},
            datetime.date(2010, 1, 1): {'<label>': 12},
            datetime.date(2010, 2, 1): {'<label>': 45}
            ...
        },
        ...]
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


def _cursor():
    """Return a DB cursor for reading."""
    return connections[router.db_for_read(Metric)].cursor()
