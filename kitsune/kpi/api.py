from operator import itemgetter
from datetime import date, timedelta

from django.conf import settings
from django.db import connections, router
from django.db.models import Count, F

from tastypie import fields
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.cache import SimpleCache
from tastypie.resources import Resource

from kitsune.kpi.models import (
    Metric, MetricKind, AOA_CONTRIBUTORS_METRIC_CODE,
    KB_ENUS_CONTRIBUTORS_METRIC_CODE, KB_L10N_CONTRIBUTORS_METRIC_CODE,
    L10N_METRIC_CODE, SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE,
    VISITORS_METRIC_CODE)
from kitsune.questions.models import Question, Answer, AnswerVote
from kitsune.wiki.models import HelpfulVote


class CachedResource(Resource):
    def obj_get_list(self, request=None, **kwargs):
        """Override ``obj_get_list`` to use the cache."""
        if request:
            # Add request query params to cache key.
            kwargs.update(**request.GET.dict())
        cache_key = self.generate_cache_key('list', **kwargs)
        obj_list = self._meta.cache.get(cache_key)

        if obj_list is None:
            obj_list = self.get_object_list(request)
            self._meta.cache.set(cache_key, obj_list, timeout=60 * 60 * 3)

        return obj_list


class WriteOnlyBasicAuthentication(BasicAuthentication):
    """Authenticator that prompts for credentials only for write requests."""
    def is_authenticated(self, request, **kwargs):
        if request.method == 'GET':
            return True
        return super(WriteOnlyBasicAuthentication, self).is_authenticated(
                request, **kwargs)


class PermissionAuthorization(Authorization):
    """Authorization which allows all users to make read-only requests and
    users with a certain permission to write."""

    def __init__(self, write=None):
        self.write_perm = write

    def is_authorized(self, request, object=None):
        # Supports just GET and POST so far
        if request.method == 'GET':
            return True
        elif request.method == 'POST':
            return request.user.has_perm(self.write_perm)
        return False


class Struct(object):
    """Convert a dict to an object"""
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __unicode__(self):
        return unicode(self.__dict__)


class SearchClickthroughMeta(object):
    """Abstract Meta inner class for search clickthrough resources"""
    # The Resource metaclass isn't smart enough to merge in attributes from
    # Meta classes defined in subclasses of an abstract resource, like Django's
    # ORM metaclass is. There's might be a supported way, but I'm really sick
    # of reading tastypie docs (and source).
    object_class = Struct
    authentication = WriteOnlyBasicAuthentication()
    authorization = PermissionAuthorization(write='kpi.add_metric')


class SearchClickthroughResource(CachedResource):
    """Clickthrough ratio for searches over one period

    Represents a ratio of {clicks of results}/{total searches} for one engine.

    """
    #: Date of period start. Assumes 1-day periods.
    start = fields.DateField('start')
    #: How many searches had (at least?) 1 result clicked
    clicks = fields.IntegerField('clicks', default=0)
    #: How many searches were performed with this engine
    searches = fields.IntegerField('searches', default=0)

    @property
    def searches_kind(self):
        return 'search clickthroughs:%s:searches' % self.engine

    @property
    def clicks_kind(self):
        return 'search clickthroughs:%s:clicks' % self.engine

    def obj_get(self, request=None, **kwargs):
        """Fetch a particular ratio by start date."""
        raise NotImplementedError

    def get_object_list(self, request=None, **kwargs):
        """Return all the ratios.

        Or, if a ``min_start`` query param is present, return the (potentially
        limited) ratios later than or equal to that. ``min_start`` should be
        something like ``2001-07-30``.

        If, somehow, half a ratio is missing, that ratio is not returned.

        """
        # Get min_start from query string and validate it.
        min_start = request.GET.get('min_start')
        if min_start:
            try:
                _parse_date(min_start)
            except (ValueError, TypeError):
                min_start = None

        # I'm not sure you can join a table to itself with the ORM.
        cursor = _cursor()
        cursor.execute(  # n for numerator, d for denominator
            'SELECT n.start, n.value, d.value '
            'FROM kpi_metric n '
            'INNER JOIN kpi_metric d ON n.start=d.start '
            'WHERE n.kind_id=(SELECT id FROM kpi_metrickind WHERE code=%s) '
            'AND d.kind_id=(SELECT id FROM kpi_metrickind WHERE code=%s) ' +
            ('AND n.start>=%s' if min_start else ''),
            (self.clicks_kind, self.searches_kind) +
                ((min_start,) if min_start else ()))
        return [Struct(start=s, clicks=n, searches=d) for
                s, n, d in reversed(cursor.fetchall())]

    def obj_create(self, bundle, request=None, **kwargs):
        def create_metric(kind, value_field, data):
            """Given POSTed data, create a Metric.

            Assume day-long buckets for the moment.

            """
            start = date(*_parse_date(data['start']))
            Metric.objects.create(kind=MetricKind.objects.get(code=kind),
                                  start=start,
                                  end=start + timedelta(days=1),
                                  value=data[value_field])

        create_metric(self.searches_kind, 'searches', bundle.data)
        create_metric(self.clicks_kind, 'clicks', bundle.data)

    def get_resource_uri(self, bundle_or_obj):
        """Return a fake answer; we don't care, for now."""
        return ''


class ElasticClickthroughResource(SearchClickthroughResource):
    engine = 'elastic'

    class Meta(SearchClickthroughMeta):
        resource_name = 'elastic-clickthrough-rate'


class QuestionsResource(CachedResource):
    """Returns metrics related to questions.

    * Number of questions asked
    * Number of questions responded to within 72 hours
    * Number of questions solved
    """
    date = fields.DateField('date')
    questions = fields.IntegerField('questions', default=0)
    responded_72 = fields.IntegerField('responded_72', default=0)
    responded_24 = fields.IntegerField('responded_24', default=0)
    solved = fields.IntegerField('solved', default=0)

    def get_object_list(self, request):
        # Set up the query for the data we need.
        qs = _daily_qs_for(Question)

        # All answers that were created within 3 days of the question.
        aq_72 = Answer.objects.filter(
                created__lt=F('question__created') + timedelta(days=3))
        # Questions of said answers.
        rs_72 = qs.filter(id__in=aq_72.values_list('question'))

        # All answers that were created within 24 hours of the question.
        aq_24 = Answer.objects.filter(
                created__lt=F('question__created') + timedelta(hours=24))
        # Questions of said answers.
        rs_24 = qs.filter(id__in=aq_24.values_list('question'))

        # Questions with a solution.
        qs_with_solutions = qs.exclude(solution_id=None)

        return merge_results(
            questions=qs,
            solved=qs_with_solutions,
            responded_72=rs_72,
            responded_24=rs_24)

    class Meta(object):
        cache = SimpleCache()
        resource_name = 'kpi_questions'
        allowed_methods = ['get']


class VoteResource(CachedResource):
    """Returns the number helpful votes for Articles and Answers."""
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


class KBVoteResource(CachedResource):
    """Returns the number helpful votes for KB Articles."""
    date = fields.DateField('date')
    kb_helpful = fields.IntegerField('kb_helpful', default=0)
    kb_votes = fields.IntegerField('kb_votes', default=0)

    def get_object_list(self, request):
        # Set up the queries for the data we need

        locale = request.GET.get('locale')

        qs_kb_votes = HelpfulVote.objects.filter(
            created__gte=date(2011, 1, 1))

        if locale:
            qs_kb_votes = qs_kb_votes.filter(
                revision__document__locale=locale)

        qs_kb_votes = (qs_kb_votes
            .extra(
                select={
                    'day': 'extract( day from wiki_helpfulvote.created )',
                    'month': 'extract( month from wiki_helpfulvote.created )',
                    'year': 'extract( year from wiki_helpfulvote.created )',})
            .values('year', 'month', 'day')
            .annotate(count=Count('created')))

        # Filter on helpful
        qs_kb_helpful_votes = qs_kb_votes.filter(helpful=True)

        return merge_results(
            kb_votes=qs_kb_votes, kb_helpful=qs_kb_helpful_votes)

    class Meta(object):
        cache = SimpleCache()
        resource_name = 'kpi_kb_vote'
        allowed_methods = ['get']


class ActiveContributorsResource(CachedResource):
    """Returns the number of active contributors.

    * en-US KB contributors
    * non-en-US contributors
    * Support Forum contributors
    * Army of Awesome contributors
    """
    date = fields.DateField('date')
    en_us = fields.IntegerField('en_us', default=0)
    non_en_us = fields.IntegerField('non_en_us', default=0)
    support_forum = fields.IntegerField('support_forum', default=0)
    aoa = fields.IntegerField('aoa', default=0)

    def get_object_list(self, request):
        # Set up the queries for the data we need
        kind = MetricKind.objects.get(code=KB_ENUS_CONTRIBUTORS_METRIC_CODE)
        en_us = Metric.objects.filter(kind=kind).order_by('-start')

        kind = MetricKind.objects.get(code=KB_L10N_CONTRIBUTORS_METRIC_CODE)
        l10n = Metric.objects.filter(kind=kind).order_by('-start')

        kind = MetricKind.objects.get(
            code=SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE)
        answers = Metric.objects.filter(kind=kind).order_by('-start')

        kind = MetricKind.objects.get(code=AOA_CONTRIBUTORS_METRIC_CODE)
        aoa = Metric.objects.filter(kind=kind).order_by('-start')

        # Put all the results in a dict with the date as the key.
        results_dict = {}

        def merge_results(metrics_qs, label):
            for metric in metrics_qs:
                results_dict.setdefault(metric.end, {})[label] = metric.value

        merge_results(en_us, 'en_us')
        merge_results(l10n, 'non_en_us')
        merge_results(answers, 'support_forum')
        merge_results(aoa, 'aoa')

        # Convert that to a list of dicts.
        results_list = [dict(date=k, **v) for k, v in results_dict.items()]

        return [Struct(**x) for x in sorted(
            results_list, key=itemgetter('date'), reverse=True)]

    class Meta:
        cache = SimpleCache()
        resource_name = 'kpi_active_contributors'
        allowed_methods = ['get']


class VisitorsResource(CachedResource):
    """Returns the number of unique visitors per day."""
    date = fields.DateField('date')
    visitors = fields.IntegerField('visitors', default=0)

    def get_object_list(self, request):
        # Set up the query for the data we need
        kind = MetricKind.objects.get(code=VISITORS_METRIC_CODE)
        qs = Metric.objects.filter(kind=kind).order_by('-start')

        return [Struct(date=m.start, visitors=m.value) for m in qs]

    class Meta(object):
        cache = SimpleCache()
        resource_name = 'kpi_visitors'
        allowed_methods = ['get']


class L10nCoverageResource(CachedResource):
    """Returns the L10n coverage per day."""
    date = fields.DateField('date')
    coverage = fields.IntegerField('coverage', default=0)

    def get_object_list(self, request):
        # Set up the query for the data we need
        kind = MetricKind.objects.get(code=L10N_METRIC_CODE)
        qs = Metric.objects.filter(kind=kind).order_by('-start')

        return [Struct(date=m.start, coverage=m.value) for m in qs]

    class Meta(object):
        cache = SimpleCache()
        resource_name = 'kpi_l10n_coverage'
        allowed_methods = ['get']


def _daily_qs_for(model_cls):
    """Return the daily grouped queryset we need for model_cls."""
    # Limit to newer than 2011/1/1 and active creators.
    return model_cls.objects.filter(
        created__gte=date(2011, 1, 1), creator__is_active=1).extra(
            select={
                'day': 'extract( day from created )',
                'month': 'extract( month from created )',
                'year': 'extract( year from created )',
            }).values('year', 'month', 'day').annotate(
                count=Count('created'))


def _qs_for(model_cls):
    """Return the monthly grouped queryset we need for model_cls."""
    return model_cls.objects.filter(created__gte=date(2011, 1, 1)).extra(
        select={
            'day': 'extract( day from created )',
            'month': 'extract( month from created )',
            'year': 'extract( year from created )',
        }).values('year', 'month', 'day').annotate(count=Count('created'))


def _start_date():
    """The date from which we start querying monthly data."""
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
        yield dict((date(x['year'], x['month'], x.get('day', 1)),
                   {label: x['count']}) for x in qs)


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


def _parse_date(text):
    """Parse a text date like ``"2004-08-30`` into a triple of numbers.

    May fling ValueErrors or TypeErrors around if the input or date is invalid.
    It should at least be a string--I mean, come on.

    """
    return tuple(int(i) for i in text.split('-'))
