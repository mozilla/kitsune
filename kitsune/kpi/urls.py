from django.conf.urls import patterns, url, include

from tastypie.api import Api

from kitsune.kpi.api import (
    QuestionsResource, VoteResource, ActiveContributorsResource,
    ElasticClickthroughResource, VisitorsResource, L10nCoverageResource,
    KBVoteResource, ExitSurveyResultsResource)


v1_api = Api(api_name='v1')
v1_api.register(QuestionsResource())
v1_api.register(VoteResource())
v1_api.register(KBVoteResource())
v1_api.register(ActiveContributorsResource())
v1_api.register(ElasticClickthroughResource())
v1_api.register(VisitorsResource())
v1_api.register(L10nCoverageResource())
v1_api.register(ExitSurveyResultsResource())


urlpatterns = patterns(
    'kitsune.kpi.views',
    url(r'^dashboard$', 'dashboard',
        name='kpi.dashboard'),
    (r'^api/', include(v1_api.urls)),
)
