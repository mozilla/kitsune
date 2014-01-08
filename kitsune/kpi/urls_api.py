from django.conf.urls import patterns, url

from kitsune.kpi import api

urlpatterns = patterns(
    '',
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
)
