from django.conf.urls.defaults import patterns, url, include

from kpi.api import (QuestionsResource, VoteResource,
                     ActiveContributorsResource, ElasticClickthroughResource,
                     VisitorsResource, L10nCoverageResource, KBVoteResource)
from tastypie.api import Api


v1_api = Api(api_name='v1')
v1_api.register(QuestionsResource())
v1_api.register(VoteResource())
v1_api.register(KBVoteResource())
v1_api.register(ActiveContributorsResource())
v1_api.register(ElasticClickthroughResource())
v1_api.register(VisitorsResource())
v1_api.register(L10nCoverageResource())


urlpatterns = patterns('kpi.views',
    url(r'^dashboard$', 'dashboard',
        name='kpi.dashboard'),
    (r'^api/', include(v1_api.urls)),
)
