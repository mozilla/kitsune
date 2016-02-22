from django.conf.urls import patterns, url, include
from rest_framework import routers

from kitsune.kpi import api
from kitsune.kpi.models import (CONTRIBUTORS_CSAT_METRIC_CODE, AOA_CONTRIBUTORS_CSAT_METRIC_CODE,
                                SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE,
                                KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE,
                                KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE)

router = routers.SimpleRouter()
router.register(r'cohort', api.CohortViewSet)

urlpatterns = patterns(
    '',
    url(r'^api/v1/kpi/csat-contributors/?$',
        api.CSATMetricList.as_view(code=CONTRIBUTORS_CSAT_METRIC_CODE),
        name='api.kpi.csat-contributors'),
    url(r'^api/v1/kpi/csat-contributors/aoa/?$',
        api.CSATMetricList.as_view(code=AOA_CONTRIBUTORS_CSAT_METRIC_CODE),
        name='api.kpi.csat-contributors-aoa'),
    url(r'^api/v1/kpi/csat-contributors/support-forum/?$',
        api.CSATMetricList.as_view(code=SUPPORT_FORUM_CONTRIBUTORS_CSAT_METRIC_CODE),
        name='api.kpi.csat-contributors-support-forum'),
    url(r'^api/v1/kpi/csat-contributors/kb-enus/?$',
        api.CSATMetricList.as_view(code=KB_ENUS_CONTRIBUTORS_CSAT_METRIC_CODE),
        name='api.kpi.csat-contributors-kb-enus'),
    url(r'^api/v1/kpi/csat-contributors/kb-l10n/?$',
        api.CSATMetricList.as_view(code=KB_L10N_CONTRIBUTORS_CSAT_METRIC_CODE),
        name='api.kpi.csat-contributors-kb-l10n'),
    url(r'^api/v1/kpi/l10n-coverage/?$', api.L10nCoverageMetricList.as_view(),
        name='api.kpi.l10n-coverage'),
    url(r'^api/v1/kpi/exit-survey/?$', api.ExitSurveyMetricList.as_view(),
        name='api.kpi.exit-survey'),
    url(r'^api/v1/kpi/visitors/?$', api.VisitorsMetricList.as_view(),
        name='api.kpi.visitors'),
    url(r'^api/v1/kpi/contributors/?$', api.ContributorsMetricList.as_view(),
        name='api.kpi.contributors'),
    url(r'^api/v1/kpi/kb-votes/?$', api.KBVoteMetricList.as_view(),
        name='api.kpi.kb-votes'),
    url(r'^api/v1/kpi/votes/?$', api.VoteMetricList.as_view(),
        name='api.kpi.votes'),
    url(r'^api/v1/kpi/questions/?$', api.QuestionsMetricList.as_view(),
        name='api.kpi.questions'),
    url(r'^api/v1/kpi/search-ctr/?$',
        api.SearchClickthroughMetricList.as_view(),
        name='api.kpi.search-ctr'),
    url(r'^api/2/', include(router.urls)),
)
