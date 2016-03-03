from collections import defaultdict
from datetime import date, timedelta
from operator import itemgetter

from django.core.cache import cache
from django.db import connections, router
from django.db.models import Count, F

from rest_framework import filters, serializers, viewsets
from rest_framework.filters import django_filters
from rest_framework.views import APIView
from rest_framework.response import Response

from kitsune.kpi.models import (
    Cohort, Metric, MetricKind, RetentionMetric, AOA_CONTRIBUTORS_METRIC_CODE,
    KB_ENUS_CONTRIBUTORS_METRIC_CODE, KB_L10N_CONTRIBUTORS_METRIC_CODE, L10N_METRIC_CODE,
    SUPPORT_FORUM_CONTRIBUTORS_METRIC_CODE, VISITORS_METRIC_CODE, EXIT_SURVEY_YES_CODE,
    EXIT_SURVEY_NO_CODE, EXIT_SURVEY_DONT_KNOW_CODE)
from kitsune.questions.models import Question, Answer, AnswerVote
from kitsune.wiki.models import HelpfulVote


class CachedAPIView(APIView):
    """An APIView that caches the objects to be returned.

    Subclasses must implement the get_objects() method.
    """

    def _cache_key(self, request):
        params = []
        for key, value in request.GET.items():
            params.append("%s=%s" % (key, value))
        return u'{viewname}:{params}'.format(
            viewname=self.__class__.__name__,
            params=u':'.join(sorted(params)))

    def get(self, request):
        cache_key = self._cache_key(request)

        objs = cache.get(cache_key)
        if objs is None:
            objs = self.get_objects(request)
            cache.add(cache_key, objs, 60 * 60 * 3)

        return Response({
            'objects': objs
        })

    def get_objects(self, request):
        """Returns a list of dicts the API view will return."""
        raise NotImplementedError('Must be overriden in subclass')


class SearchClickthroughMetricList(CachedAPIView):
    """The API list view for search click-through rate metrics."""

    engine = 'elastic'

    @property
    def searches_kind(self):
        return 'search clickthroughs:%s:searches' % self.engine

    @property
    def clicks_kind(self):
        return 'search clickthroughs:%s:clicks' % self.engine

    def get_objects(self, request):
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
        # n for numerator, d for denominator
        query = """
            SELECT n.start, n.value, d.value
            FROM kpi_metric n
            INNER JOIN kpi_metric d ON n.start=d.start
            WHERE n.kind_id=(SELECT id FROM kpi_metrickind WHERE code=%s)
            AND d.kind_id=(SELECT id FROM kpi_metrickind WHERE code=%s)
            """ + ('AND n.start>=%s' if min_start else '')
        args = [self.clicks_kind, self.searches_kind]
        if min_start:
            args.append(min_start)
        cursor.execute(query, args)
        return [dict(start=s, clicks=n, searches=d) for
                s, n, d in reversed(cursor.fetchall())]


class QuestionsMetricList(CachedAPIView):
    """The API list view for support forum metrics.

    * Number of questions asked
    * Number of questions responded to within 24 hours
    * Number of questions responded to within 72 hours
    * Number of questions solved
    """

    def get_objects(self, request):
        # Set up the queries for the data we need
        locale = request.GET.get('locale')
        product = request.GET.get('product')

        # Set up the query for the data we need.
        qs = _daily_qs_for(Question)

        # Don't count locked questions
        qs = qs.exclude(is_locked=True)

        # Don't count spam questions
        qs = qs.exclude(is_spam=True)

        if locale:
            qs = qs.filter(locale=locale)

        if product:
            qs = qs.filter(product__slug=product)

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


class VoteMetricList(CachedAPIView):
    """The API list view for vote metrics."""

    def get_objects(self, request):
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


class KBVoteMetricList(CachedAPIView):
    """The API list view for KB vote metrics."""

    def get_objects(self, request):
        # Set up the queries for the data we need
        locale = request.GET.get('locale')
        product = request.GET.get('product')

        qs_kb_votes = HelpfulVote.objects.filter(
            created__gte=date(2011, 1, 1))

        if locale:
            qs_kb_votes = qs_kb_votes.filter(
                revision__document__locale=locale)

        if product and product != 'null':
            qs_kb_votes = qs_kb_votes.filter(
                revision__document__products__slug=product)  # WHOA

        qs_kb_votes = (
            qs_kb_votes.extra(
                select={
                    'day': 'extract( day from wiki_helpfulvote.created )',
                    'month': 'extract( month from wiki_helpfulvote.created )',
                    'year': 'extract( year from wiki_helpfulvote.created )',
                })
            .values('year', 'month', 'day')
            .annotate(count=Count('created')))

        # Filter on helpful
        qs_kb_helpful_votes = qs_kb_votes.filter(helpful=True)

        return merge_results(
            kb_votes=qs_kb_votes, kb_helpful=qs_kb_helpful_votes)


class ContributorsMetricList(CachedAPIView):
    """The API list view for active contributor metrics.

    * en-US KB contributors
    * non-en-US contributors
    * Support Forum contributors
    * Army of Awesome contributors
    """

    def get_objects(self, request):
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

        return [dict(**x) for x in sorted(
            results_list, key=itemgetter('date'), reverse=True)]


class VisitorsMetricList(CachedAPIView):
    """The API list view for visitor metrics."""

    def get_objects(self, request):
        # Set up the query for the data we need
        kind = MetricKind.objects.get(code=VISITORS_METRIC_CODE)
        qs = Metric.objects.filter(kind=kind).order_by('-start')

        return [dict(date=m.start, visitors=m.value) for m in qs]


class L10nCoverageMetricList(CachedAPIView):
    """The API list view for L10n coverage metrics."""

    def get_objects(self, request):
        # Set up the query for the data we need
        kind = MetricKind.objects.get(code=L10N_METRIC_CODE)
        qs = Metric.objects.filter(kind=kind).order_by('-start')

        return [dict(date=m.start, coverage=m.value) for m in qs]


class ExitSurveyMetricList(CachedAPIView):
    """The API list view for exit survey metrics."""

    def get_objects(self, request):
        # Set up the queries for the data we need
        kind = MetricKind.objects.get(code=EXIT_SURVEY_YES_CODE)
        yes = Metric.objects.filter(kind=kind).order_by('-start')

        kind = MetricKind.objects.get(code=EXIT_SURVEY_NO_CODE)
        no = Metric.objects.filter(kind=kind).order_by('-start')

        kind = MetricKind.objects.get(code=EXIT_SURVEY_DONT_KNOW_CODE)
        dont_know = Metric.objects.filter(kind=kind).order_by('-start')

        # Put all the results in a dict with the date as the key.
        results_dict = {}

        def merge_results(metrics_qs, label):
            for metric in metrics_qs:
                results_dict.setdefault(metric.end, {})[label] = metric.value

        merge_results(yes, 'yes')
        merge_results(no, 'no')
        merge_results(dont_know, 'dont_know')

        # Convert that to a list of dicts.
        results_list = [dict(date=k, **v) for k, v in results_dict.items()]

        return [dict(**x) for x in sorted(
            results_list, key=itemgetter('date'), reverse=True)]


class CSATMetricList(CachedAPIView):
    """The API list view for contributor CSAT metrics"""
    code = None

    def get_objects(self, request):
        kind = MetricKind.objects.get(code=self.code)
        since = date.today() - timedelta(days=30)
        metrics = Metric.objects.filter(start__gte=since, kind=kind).order_by('-start')

        return [{'date': m.start, 'csat': m.value} for m in metrics]


def _daily_qs_for(model_cls):
    """Return the daily grouped queryset we need for model_cls."""
    # Limit to newer than 2011/1/1 and active creators.
    return (model_cls.objects
            .filter(created__gte=date(2011, 1, 1), creator__is_active=1)
            .extra(select={
                'day': 'extract( day from created )',
                'month': 'extract( month from created )',
                'year': 'extract( year from created )',
            })
            .values('year', 'month', 'day')
            .annotate(count=Count('created')))


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
    kwargs = {
        <label>=[
            {'count': 45, 'month': 2L, 'year': 2010L},
            {'count': 6, 'month': 2L, 'year': 2010L},   # Note duplicate date
            {'count': 12, 'month': 1L, 'year': 2010L},
            {'count': 1, 'month': 12L, 'year': 2009L},
            ...
        ],
        <label>=[{...},...],
    }
    returns [
        {
            datetime.date(2009, 12, 1): {'<label>': 1},
            datetime.date(2010, 1, 1): {'<label>': 12},
            datetime.date(2010, 2, 1): {'<label>': 51}  # Note summed counts
            ...
        },
        ...]
    """
    for label, qs in kwargs.iteritems():
        res = defaultdict(lambda: {label: 0})
        # For each date mentioned in qs, sum up the counts for that day
        # Note: days may be duplicated
        for x in qs:
            key = date(x['year'], x['month'], x.get('day', 1))
            res[key][label] += x['count']
        yield res


def merge_results(**kwargs):
    res_dict = reduce(_merge_results, _remap_date_counts(**kwargs))
    res_list = [dict(date=k, **v) for k, v in res_dict.items()]
    return [dict(**x)
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


class RetentionMetricSerializer(serializers.ModelSerializer):
    start = serializers.DateField()
    end = serializers.DateField()
    size = serializers.IntegerField()

    class Meta:
        model = RetentionMetric
        fields = (
            'start',
            'end',
            'size',
        )


class CohortSerializer(serializers.ModelSerializer):
    kind = serializers.SlugRelatedField(slug_field='code', read_only=True)
    start = serializers.DateField()
    end = serializers.DateField()
    size = serializers.IntegerField()
    retention_metrics = RetentionMetricSerializer(many=True)

    class Meta:
        model = Cohort
        fields = (
            'kind',
            'start',
            'end',
            'size',
            'retention_metrics',
        )


class CohortFilter(django_filters.FilterSet):
    kind = django_filters.CharFilter(name='kind__code')
    start = django_filters.DateFilter(lookup_type='gte')
    end = django_filters.DateFilter(lookup_type='lte')

    class Meta:
        model = Cohort
        fields = (
            'kind',
            'start',
            'end',
        )


class CohortViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cohort.objects.all()
    serializer_class = CohortSerializer
    filter_class = CohortFilter
    filter_backends = [
        filters.DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    ordering_fields = [
        'start',
    ]
    ordering = ('start',)
